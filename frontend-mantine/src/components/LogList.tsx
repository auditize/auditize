import { useState, useEffect } from 'react';
import { Table, Button, Center, Container, Select, Group, TextInput } from '@mantine/core';
import { useInfiniteQuery, useQuery } from '@tanstack/react-query';
import { labelize } from './utils';
import { getLogs, getAllLogEventNames, getAllLogEventCategories, getAllLogActorTypes, getAllLogResourceTypes, getAllLogTagCategories, getAllLogNodes, LogFilterParams } from '../services/logs';
import { ControlledTreeEnvironment, Tree, TreeItem, TreeItemIndex } from 'react-complex-tree';
import 'react-complex-tree/lib/style-modern.css';

type ValueChangeEvent = {name: string, value: string | undefined};
type OnValueChangeEvent = (event: ValueChangeEvent) => void;

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
  {label, name, queryKey, queryFn, selectedItem, onChange}:
  {label: string, name: string, queryKey: any, queryFn: () => Promise<string[]>, selectedItem?: string, onChange: OnValueChangeEvent}) {
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
      onChange={(value, option) => onChange({name, value: value || undefined})}
      placeholder={isPending ? "Loading..." : label}
      clearable
      display="flex"
    />
  );
}

function EventCategorySelector({category, onChange}: {category?: string, onChange: OnValueChangeEvent}) {
  return (
    <PaginatedSelector
      name="eventCategory"
      label="Event category"
      queryKey={['logEventCategory']} queryFn={getAllLogEventCategories}
      selectedItem={category} onChange={onChange} />
  );
}

function EventNameSelector(
  {name, category, onChange}: {name?: string, category?: string, onChange: OnValueChangeEvent}) {
  return (
    <PaginatedSelector
      name='eventName'
      label="Event name"
      queryKey={['logEventNames', category]} queryFn={() => getAllLogEventNames(category)}
      selectedItem={name} onChange={onChange} />
  );
}

function ActorTypeSelector({type, onChange}: {type?: string, onChange: OnValueChangeEvent}) {
  return (
    <PaginatedSelector
      name='actorType'
      label="Actor type"
      queryKey={['logActorType']} queryFn={getAllLogActorTypes}
      selectedItem={type} onChange={onChange} />
  );
}

function ResourceTypeSelector({type, onChange}: {type?: string, onChange: OnValueChangeEvent}) {
  return (
    <PaginatedSelector
      name='resourceType'
      label="Resource type"
      queryKey={['logResourceType']} queryFn={getAllLogResourceTypes}
      selectedItem={type} onChange={onChange} />
  );
}

function TagCategorySelector({category, onChange}: {category?: string, onChange: OnValueChangeEvent}) {
  return (
    <PaginatedSelector
      name='tagCategory'
      label="Tag category"
      queryKey={['logTagCategory']} queryFn={getAllLogTagCategories}
      selectedItem={category} onChange={onChange} />
  );
}

function NodeSelector({nodeId, onChange}: {nodeId: string | null, onChange: OnValueChangeEvent}) {
  const [items, setItems] = useState<Record<TreeItemIndex, TreeItem<any>>>({
    root: {
      index: 'root',
      children: [],
      isFolder: true,
      data: 'Root',
    }
  });
  const [expandedItems, setExpandedItems] = useState<TreeItemIndex[]>([]);

  const logNodeToTreeNode = (node: LogNode): TreeItem => ({
    index: node.id,
    children: [],
    isFolder: node.has_children,
    data: node.name,
  });

  const logNodesToTreeNodes = (nodes: LogNode[]): Record<TreeItemIndex, TreeItem<any>> => {
    const treeItems: Record<TreeItemIndex, TreeItem<any>> = {};
    nodes.forEach((node) => treeItems[node.id] = logNodeToTreeNode(node));
    return treeItems;
  }

  const addItems = (nodes: LogNode[], parentItem: TreeItemIndex) => {
    const newItems = logNodesToTreeNodes(nodes);
    const parent = {...items[parentItem]};
    parent.children = nodes.map((node) => node.id);
    setItems({...items, ...newItems, [parentItem]: parent});
  }

  useEffect(() => {
    getAllLogNodes().then((nodes) => {
      addItems(nodes, 'root');
    });
  }, []);

  const expandItem = (item: TreeItem<any>) => {
    if (item.children?.length === 0)
      getAllLogNodes(item.index as string).then((nodes) => addItems(nodes, item.index));
    setExpandedItems([...expandedItems, item.index]);
  };

  const collapseItem = (item: TreeItem<any>) => {
    const arrayIdx = expandedItems.indexOf(item.index);
    if (arrayIdx != -1) {
      const updatedExpandedItems = [...expandedItems];
      updatedExpandedItems.splice(arrayIdx, 1);
      setExpandedItems(updatedExpandedItems);
    }
  };

  const selectItem = (index: TreeItemIndex) => {
    onChange({name: 'nodeId', value: index as string});
  }

  return (
    <ControlledTreeEnvironment
      items={items}
      viewState={{
        ['nodeSelector']: {
          selectedItems: [nodeId as TreeItemIndex] || undefined,
          expandedItems,
        },
      }}
      onExpandItem={expandItem}
      onCollapseItem={collapseItem}
      onSelectItems={(items: TreeItemIndex[]) => selectItem(items[0])}
      getItemTitle={(item) => item.data}
    >
      <Tree treeId='nodeSelector' rootItem='root' />
    </ControlledTreeEnvironment>
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
    <Container size="xl" p="20px">
      <LogTable logs={data.pages.flatMap((page) => page.logs)} footer={footer} />
    </Container>
  );
};

function LogFilters({onChange}: {onChange: (filter: LogFilterParams) => void}){
  const [params, setParams] = useState<LogFilterParams>({});

  const changeParam = ({name, value}: ValueChangeEvent) => {
    const update = {[name]: value};
    if (name === 'eventCategory')
      update['eventName'] = undefined;
    console.log("Updating filter params", update);
    setParams({...params, ...update});
  }

  return (
    <Container>
      {/* Event criteria */}
      <Group m={"1rem"}>
        <EventCategorySelector
          category={params.eventCategory}
          onChange={changeParam}/>
        <EventNameSelector
          name={params.eventName} category={params.eventCategory}
          onChange={changeParam}/>
      </Group>

      {/* Actor criteria */}
      <Group m={"1rem"}>
        <ActorTypeSelector
          type={params.actorType}
          onChange={changeParam}/>
        <TextInput
          placeholder="Actor name"
          value={params.actorName}
          onChange={(e) => changeParam({name: 'actorName', value: e.target.value})}
          display={"flex"}/>
      </Group>

      {/* Resource criteria */}
      <Group m={"1rem"}>
        <ResourceTypeSelector
          type={params.resourceType}
          onChange={changeParam}/>
        <TextInput
          placeholder="Resource name"
          value={params.resourceName}
          onChange={(e) => changeParam({name: 'resourceName', value: e.target.value})}
          display={"flex"}/>
      </Group>

      {/* Tag criteria */}
      <Group m={"1rem"}>
        <TagCategorySelector
          category={params.tagCategory}
          onChange={changeParam}/>
        <TextInput
          placeholder="Tag name"
          value={params.tagName}
          onChange={(e) => changeParam({name: 'tagName', value: e.target.value})}
          display="flex"/>
        <TextInput
          placeholder="Tag id"
          value={params.tagId}
          onChange={(e) => changeParam({name: 'tagId', value: e.target.value})}
          display="flex"/>
      </Group>

      {/* Node criteria */}
      <Group m="1rem">
        <NodeSelector nodeId={params.nodeId || null} onChange={changeParam} />
      </Group>

      {/* Apply button */}
      <Button onClick={() => onChange(params)}>
        Apply filters
      </Button>
    </Container>
  );
}

export function LogList() {
  const [filter, setFilter] = useState<LogFilterParams>({});
  
  return (
    <div>
      <LogFilters onChange={setFilter} />
      <LogLoader filter={filter} />
    </div>
  );
}
