import { useEffect, useRef, useState, useReducer } from 'react';
import { rem, Table, Button, Center, Container, Select, Group, Stack, TextInput, Popover, Space, Anchor } from '@mantine/core';
import { DateTimePicker } from '@mantine/dates';
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

const emptyLogFilterParams: LogFilterParams = {
  eventCategory: "",
  eventName: "",
  actorType: "",
  actorName: "",
  resourceType: "",
  resourceName: "",
  tagCategory: "",
  tagName: "",
  tagId: "",
  nodeId: "",
  since: null,
  until: null
};

function LogTable(
  {logs, footer, onTableFilterChange}:
  {logs: Log[], footer: React.ReactNode, onTableFilterChange: (name: string, value: string) => void}) {
  const rows = logs.map((log) => (
    <Table.Tr key={log.id}>
      <Table.Td>{log.saved_at}</Table.Td>
      <Table.Td>
        <Anchor onClick={() => onTableFilterChange('eventName', log.event.name)} underline='hover'>
          {labelize(log.event.name)}
        </Anchor>
      </Table.Td>
      <Table.Td>
        <Anchor onClick={() => onTableFilterChange('eventCategory', log.event.category)} underline='hover'>
          {labelize(log.event.category)}
        </Anchor>
      </Table.Td>
      <Table.Td>
        {
          log.actor ?
            <Anchor onClick={() => onTableFilterChange('actorName', log.actor!.name)} underline='hover'>
              {log.actor.name}
            </Anchor> :
            null
        }
        </Table.Td>
      <Table.Td>
        {
          log.resource ?
            <Anchor onClick={() => onTableFilterChange('resourceName', log.resource!.name)} underline='hover'>
              {log.resource.name}
            </Anchor> :
            null
        }
      </Table.Td>
      <Table.Td>
        {
          log.resource ?
            <Anchor onClick={() => onTableFilterChange('resourceType', log.resource!.type)} underline='hover'>
              {log.resource.type}
            </Anchor> :
            null
        }
      </Table.Td>
      <Table.Td>
        {
          log.node_path.map<React.ReactNode>(
            (node) => (
              // FIXME: the filter edition for the node path may not work properly if the selected node
              // has not been already loaded in the TreePicker component
              <Anchor key={node.id} onClick={() => onTableFilterChange('nodeId', node.id)} underline='hover'>
                {node.name}
              </Anchor>
            )
          ).reduce((prev, curr) => [prev, ' > ', curr])
        }
      </Table.Td>
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
      style={{width: 200}}/>
  );
}


function LogLoader(
  {filter = {}, onTableFilterChange}:
  {filter: LogFilterParams, onTableFilterChange: (name: string, value: string) => void}) {
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
    <LogTable
      logs={data.pages.flatMap((page) => page.logs)}
      footer={footer}
      onTableFilterChange={onTableFilterChange}/>
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

function LogFilterDateTimePicker(
  {placeholder, value, onChange, initToEndOfDay = false}:
  {placeholder: string, value: Date | null | undefined, onChange: (value: Date | null) => void, initToEndOfDay?: boolean}) {
    const previousValueRef = useRef<Date | null>(null);

    useEffect(() => {
      if (initToEndOfDay) {
        if (previousValueRef.current === null && value) {
          const date = new Date(value as Date);
          date.setHours(23, 59, 59);
          onChange(date);
        }
        previousValueRef.current = value || null;
      }
    });

  return (
    <DateTimePicker
      placeholder={placeholder}
      value={value}
      valueFormat='YYYY-MM-DD HH:mm'
      onChange={onChange}
      clearable
      w="14rem"
      popoverProps={{ withinPortal: false }}
      />
  );
}

interface SetParamAction {
  type: 'setParam';
  name: string;
  value: any;
}

interface ResetParamsAction {
  type: 'resetParams';
  params?: LogFilterParams;
}

function filterParamsReducer(state: LogFilterParams, action: SetParamAction | ResetParamsAction): LogFilterParams {
  console.log("filterParamsReducer", action);
  switch (action.type) {
    case 'setParam':
      const update = {[action.name]: action.value};
      if (action.name === 'eventCategory')
        update['eventName'] = "";
      return {...state, ...update};
    case 'resetParams':
      return action.params ? {...emptyLogFilterParams, ...action.params} : {...emptyLogFilterParams};
  }
}

function LogFilters({params, onChange}: {params: LogFilterParams, onChange: (filter: LogFilterParams) => void}) {
  const [editedParams, dispatch] = useReducer(filterParamsReducer, emptyLogFilterParams);
  useEffect(() => {
    dispatch({type: 'resetParams', params});
  }, [params]);

  const changeParamHandler = (name: string) =>
    (value: any) => dispatch({type: 'setParam', name, value});
  const changeTextInputParamHandler = (name: string) =>
    (e: React.ChangeEvent<HTMLInputElement>) => dispatch({type: 'setParam', name, value: e.target.value});

  const hasDate = !!(editedParams.since || editedParams.until);
  const hasEvent = !!(editedParams.eventCategory || editedParams.eventName);
  const hasActor = !!(editedParams.actorType || editedParams.actorName);
  const hasResource = !!(editedParams.resourceType || editedParams.resourceName);
  const hasTag = !!(editedParams.tagCategory || editedParams.tagName || editedParams.tagId);
  const hasNode = !!editedParams.nodeId;
  const hasFilter = hasDate || hasEvent || hasActor || hasResource || hasTag || hasNode;

  return (
    <Group p="1rem">
      {/* Time criteria */}
      <LogFilterPopover title="Date" isFilled={hasDate}>
        <LogFilterDateTimePicker
          placeholder="From"
          value={editedParams.since}
          onChange={changeParamHandler("since")}/>
        <LogFilterDateTimePicker
          placeholder="To"
          value={editedParams.until}
          onChange={changeParamHandler("until")}
          initToEndOfDay/>
      </LogFilterPopover>

      {/* Event criteria */}
      <LogFilterPopover title="Event" isFilled={hasEvent}>
        <EventCategorySelector
          category={editedParams.eventCategory}
          onChange={changeParamHandler("eventCategory")}/>
        <EventNameSelector
          name={editedParams.eventName} category={editedParams.eventCategory}
          onChange={changeParamHandler("eventName")}/>
      </LogFilterPopover>

      {/* Actor criteria */}
      <LogFilterPopover title="Actor" isFilled={hasActor}>
        <ActorTypeSelector
          type={editedParams.actorType}
          onChange={changeParamHandler("actorType")}/>
        <TextInput
          placeholder="Actor name"
          value={editedParams.actorName}
          onChange={changeTextInputParamHandler('actorName')}
          display={"flex"}/>
      </LogFilterPopover>

      {/* Resource criteria */}
      <LogFilterPopover title="Resource" isFilled={hasResource}>
        <ResourceTypeSelector
          type={editedParams.resourceType}
          onChange={changeParamHandler("resourceType")}/>
        <TextInput
          placeholder="Resource name"
          value={editedParams.resourceName}
          onChange={changeTextInputParamHandler('resourceName')}
          display={"flex"}/>
      </LogFilterPopover>

      {/* Tag criteria */}
      <LogFilterPopover title="Tag" isFilled={hasTag}>
        <TagCategorySelector
          category={editedParams.tagCategory}
          onChange={changeParamHandler("tagCategory")}/>
        <TextInput
          placeholder="Tag name"
          value={editedParams.tagName}
          onChange={changeTextInputParamHandler('tagName')}
          display="flex"/>
        <TextInput
          placeholder="Tag id"
          value={editedParams.tagId}
          onChange={changeTextInputParamHandler('tagId')}
          display="flex"/>
      </LogFilterPopover>

      {/* Node criteria */}
      <LogFilterPopover title="Node" isFilled={!!editedParams.nodeId}>
        <NodeSelector nodeId={editedParams.nodeId || null} onChange={changeParamHandler("nodeId")} />
      </LogFilterPopover>

      {/* Apply & clear buttons */}
      <Space w="l"/>
      <Button onClick={() => onChange(editedParams)}>
        Apply
      </Button>
      <Button onClick={() => dispatch({type: 'resetParams'})} disabled={!hasFilter} variant='default'>
        Clear
      </Button>
    </Group>
  );
}

export function LogList() {
  const [filter, setFilter] = useState<LogFilterParams>({...emptyLogFilterParams});

  return (
    <Container size="xl" p="20px">
      <LogFilters params={filter} onChange={setFilter} />
      <LogLoader filter={filter} onTableFilterChange={(name, value) => {
        setFilter((filter) => ({since: filter.since, until: filter.until, [name]: value}));
      }}/>
    </Container>
  );
}
