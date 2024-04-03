import { useRef, useState } from 'react';
import { rem, Table, Button, Center, Container, Select, Group, Stack, TextInput, Popover, Space } from '@mantine/core';
import { useInfiniteQuery, useQuery } from '@tanstack/react-query';
import { labelize } from './utils';
import { getLogs, getAllLogEventNames, getAllLogEventCategories, getAllLogActorTypes, getAllLogResourceTypes, getAllLogTagCategories, getAllLogNodes, LogFilterParams } from '../services/logs';
import 'rsuite/dist/rsuite-no-reset.min.css';
import { PickerHandle, TreePicker } from 'rsuite';
import { ItemDataType } from 'rsuite/esm/@types/common';
import { IconChevronUp, IconChevronDown } from '@tabler/icons-react';

function iconSize(size: any) {
  return { width: rem(size), height: rem(size) };
}

const emptyLogFilterParams = {
  eventCategory: "",
  eventName: "",
  actorType: "",
  actorName: "",
  resourceType: "",
  resourceName: "",
  tagCategory: "",
  tagName: "",
  tagId: "",
  nodeId: ""
};

function LogTable({logs, footer}: {logs: Log[], footer: React.ReactNode}) {
  const rows = logs.map((log) => (
    <Table.Tr key={log.id}>
      <Table.Td>{log.saved_at}</Table.Td>
      <Table.Td>{labelize(log.event.name)}</Table.Td>
      <Table.Td>{labelize(log.event.category)}</Table.Td>
      <Table.Td>{log.actor ? log.actor.name : null}</Table.Td>
      <Table.Td>{log.resource ? labelize(log.resource.type) : null}</Table.Td>
      <Table.Td>{log.resource ? log.resource.name : null}</Table.Td>
      <Table.Td>{log.node_path.map((n) => n.name).join(' > ')}</Table.Td>
    </Table.Tr>
  ));

  return (
    <Table>
      <Table.Thead>
        <Table.Tr>
          <Table.Th>Date</Table.Th>
          <Table.Th>Event name</Table.Th>
          <Table.Th>Event category</Table.Th>
          <Table.Th>Actor name</Table.Th>
          <Table.Th>Resource name</Table.Th>
          <Table.Th>Resource type</Table.Th>
          <Table.Th>Node</Table.Th>
        </Table.Tr>
      </Table.Thead>
      <Table.Tbody>
        {rows}
      </Table.Tbody>
      <Table.Tfoot>
        <Table.Tr>
          <Table.Th colSpan={7}>{footer}</Table.Th>
        </Table.Tr>
      </Table.Tfoot>
    </Table>
  );
}

function PaginatedSelector(
  {label, queryKey, queryFn, selectedItem, onChange}:
  {label: string, queryKey: any, queryFn: () => Promise<string[]>, selectedItem?: string, onChange: (value: string) => void}) {
  const {isPending, error, data} = useQuery({
    queryKey: queryKey,
    queryFn: queryFn,
    refetchOnWindowFocus: false
  });

  if (error)
    return <div>Error: {error.message}</div>;

  return (
    <Select
      data={data?.map((item) => ({label: labelize(item), value: item}))}
      value={selectedItem || null}
      onChange={(value) => onChange(value || "")}
      placeholder={isPending ? "Loading..." : label}
      clearable
      display="flex"
      comboboxProps={{ withinPortal: false }}
    />
  );
}

function EventCategorySelector({category, onChange}: {category?: string, onChange: (value: string) => void}) {
  return (
    <PaginatedSelector
      label="Event category"
      queryKey={['logEventCategory']} queryFn={getAllLogEventCategories}
      selectedItem={category} onChange={onChange} />
  );
}

function EventNameSelector(
  {name, category, onChange}: {name?: string, category?: string, onChange: (value: string) => void}) {
  return (
    <PaginatedSelector
      label="Event name"
      queryKey={['logEventNames', category]} queryFn={() => getAllLogEventNames(category)}
      selectedItem={name} onChange={onChange} />
  );
}

function ActorTypeSelector({type, onChange}: {type?: string, onChange: (value: string) => void}) {
  return (
    <PaginatedSelector
      label="Actor type"
      queryKey={['logActorType']} queryFn={getAllLogActorTypes}
      selectedItem={type} onChange={onChange} />
  );
}

function ResourceTypeSelector({type, onChange}: {type?: string, onChange: (value: string) => void}) {
  return (
    <PaginatedSelector
      label="Resource type"
      queryKey={['logResourceType']} queryFn={getAllLogResourceTypes}
      selectedItem={type} onChange={onChange} />
  );
}

function TagCategorySelector({category, onChange}: {category?: string, onChange: (value: string) => void}) {
  return (
    <PaginatedSelector
      label="Tag category"
      queryKey={['logTagCategory']} queryFn={getAllLogTagCategories}
      selectedItem={category} onChange={onChange} />
  );
}

function NodeSelector({nodeId, onChange}: {nodeId: string | null, onChange: (value: string) => void}) {
  const [items, setItems] = useState<ItemDataType<string>[]>([]);
  const ref = useRef<PickerHandle>(null);

  const logNodeToItem = (node: LogNode): ItemDataType<string> => ({
    value: node.id,
    label: node.name,
    children: node.has_children ? [] : undefined,
  });

  return (
    <TreePicker
      ref={ref}
      data={items}
      value={nodeId || ""}
      onSelect={(item) => onChange(item.value as string)}
      onClean={() => onChange("")}
      onOpen={() => {
        if (items.length === 0)
          getAllLogNodes().then((nodes) => setItems(nodes.map(logNodeToItem)))
        }
      }
      getChildren={async (item) => {
        // NB: beware that items are changed under the hood without using setItems by the TreePicker component
        // after getChildren has been called
        return getAllLogNodes(item.value as string).then((nodes) => {
          return nodes.map(logNodeToItem);
        });
      }}
      placeholder="Node"
      container={() => ref.current?.root?.parentElement as HTMLElement}
      searchable={false}
      style={{width: 200}}
      ></TreePicker>
  );
}


function LogLoader({filter = {}}: {filter: LogFilterParams}) {
  const { isPending, error, data, fetchNextPage, hasNextPage, isFetchingNextPage } = useInfiniteQuery({
    queryKey: ['logs', filter],
    queryFn: async ({ pageParam }: {pageParam: string | null}) => await getLogs(pageParam, filter),
    initialPageParam: null,
    getNextPageParam: (lastPage) => lastPage.nextCursor,
    refetchOnWindowFocus: false
  });

  if (isPending)
    return <div>Loading...</div>;
  
  if (error)
    return <div>Error: {error.message}</div>;
    
  const footer = (
    <Center>
      <Button
        onClick={() => fetchNextPage()}
        disabled={!hasNextPage || isFetchingNextPage}
        loading={isFetchingNextPage}>
          Load more
      </Button>
    </Center>
  );

  return (
    <LogTable logs={data.pages.flatMap((page) => page.logs)} footer={footer} />
  );
};

function LogFilterPopover({title, children, isFilled}: {title: string, children: React.ReactNode, isFilled: boolean}) {
  const [opened, setOpened] = useState(false);

  return (
    <Popover
      opened={opened}
      onClose={() => setOpened(false)}  // close on click outside
      position="bottom" withArrow keepMounted={true}>
      <Popover.Target>
        <Button
          rightSection={
            opened ?
              <IconChevronUp style={iconSize("1.15rem")}/> :
              <IconChevronDown style={iconSize("1.15rem")}/>
          }
          onClick={() => setOpened((opened_) => !opened_)}
          variant={isFilled ? 'light' : 'outline'}>
            {title}
          </Button>
      </Popover.Target>
      <Popover.Dropdown>
        <Stack>
          {children}
        </Stack>
      </Popover.Dropdown>
    </Popover>
  );
}

function LogFilters({onChange}: {onChange: (filter: LogFilterParams) => void}) {
  const [params, setParams] = useState<LogFilterParams>({...emptyLogFilterParams});

  const changeParam = (name: string, value: string) => {
    const update = {[name]: value};
    if (name === 'eventCategory')
      update['eventName'] = "";
    console.log("Updating filter params", update);
    setParams({...params, ...update});
  }
  const changeNamedParam = (name: string) => 
    (value: string) => changeParam(name, value);
  const changeTextInputParam = (name: string) =>
    (e: React.ChangeEvent<HTMLInputElement>) => changeParam(name, e.target.value);

  const hasEvent = !!(params.eventCategory || params.eventName);
  const hasActor = !!(params.actorType || params.actorName);
  const hasResource = !!(params.resourceType || params.resourceName);
  const hasTag = !!(params.tagCategory || params.tagName || params.tagId);
  const hasNode = !!params.nodeId;
  const hasFilter = hasEvent || hasActor || hasResource || hasTag || hasNode;

  return (
    <Group p="1rem">
      {/* Event criteria */}
      <LogFilterPopover title="Event" isFilled={hasEvent}>
        <EventCategorySelector
          category={params.eventCategory}
          onChange={changeNamedParam("eventCategory")}/>
        <EventNameSelector
          name={params.eventName} category={params.eventCategory}
          onChange={changeNamedParam("eventName")}/>
      </LogFilterPopover>

      {/* Actor criteria */}
      <LogFilterPopover title="Actor" isFilled={hasActor}>
        <ActorTypeSelector
          type={params.actorType}
          onChange={changeNamedParam("actorType")}/>
        <TextInput
          placeholder="Actor name"
          value={params.actorName}
          onChange={changeTextInputParam('actorName')}
          display={"flex"}/>
      </LogFilterPopover>

      {/* Resource criteria */}
      <LogFilterPopover title="Resource" isFilled={hasResource}>
        <ResourceTypeSelector
          type={params.resourceType}
          onChange={changeNamedParam("resourceType")}/>
        <TextInput
          placeholder="Resource name"
          value={params.resourceName}
          onChange={changeTextInputParam('resourceName')}
          display={"flex"}/>
      </LogFilterPopover>

      {/* Tag criteria */}
      <LogFilterPopover title="Tag" isFilled={hasTag}>
        <TagCategorySelector
          category={params.tagCategory}
          onChange={changeNamedParam("tagCategory")}/>
        <TextInput
          placeholder="Tag name"
          value={params.tagName}
          onChange={changeTextInputParam('tagName')}
          display="flex"/>
        <TextInput
          placeholder="Tag id"
          value={params.tagId}
          onChange={changeTextInputParam('tagId')}
          display="flex"/>
      </LogFilterPopover>

      {/* Node criteria */}
      <LogFilterPopover title="Node" isFilled={!!params.nodeId}>
        <NodeSelector nodeId={params.nodeId || null} onChange={changeNamedParam("nodeId")} />
      </LogFilterPopover>

      {/* Apply & clear buttons */}
      <Space w="l"/>
      <Button onClick={() => onChange(params)}>
        Apply
      </Button>
      <Button onClick={() => setParams({...emptyLogFilterParams})} disabled={!hasFilter} variant='default'>
        Clear
      </Button>
    </Group>
  );
}

export function LogList() {
  const [filter, setFilter] = useState<LogFilterParams>({});
  
  return (
    <Container size="xl" p="20px">
      <LogFilters onChange={setFilter} />
      <LogLoader filter={filter} />
    </Container>
  );
}
