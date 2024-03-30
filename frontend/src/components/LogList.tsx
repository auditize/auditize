import { useEffect, useState } from 'react';
import { DataTable } from 'primereact/datatable';
import { Column } from 'primereact/column';
import { Button } from 'primereact/button';
import { Dropdown } from 'primereact/dropdown';
import { InputText } from 'primereact/inputtext';
import { TreeNode } from 'primereact/treenode';
import { TreeSelect, TreeSelectEventNodeEvent } from 'primereact/treeselect';
import { useInfiniteQuery, useQuery } from '@tanstack/react-query';
import { labelize } from './utils';
import { getLogs, getAllLogEventNames, getAllLogEventCategories, getAllLogActorTypes, getAllLogResourceTypes, getAllLogTagCategories, getAllLogNodes, LogFilterParams } from '../services/logs';

type ValueChangeEvent = {name: string, value: string | undefined};
type OnValueChangeEvent = (event: ValueChangeEvent) => void;

function LogTable({logs, footer}: {logs: Log[], footer: React.ReactNode}) {
  const rows = logs.map((log) => ({
    createdAt: log.saved_at,
    eventName: labelize(log.event.name),
    eventCategory: labelize(log.event.category),
    actorName: log.actor ? log.actor.name : null,
    resourceType: log.resource ? labelize(log.resource.type) : null,
    resourceName: log.resource ? log.resource.name : null,
    nodePath: log.node_path.map((n) => n.name).join(' > ')
  }));

  return (
    <DataTable value={rows} footer={footer} size="small" showGridlines>
      <Column field="createdAt" header="Date" />
      <Column field="eventCategory" header="Event category" />
      <Column field="eventName" header="Event name" />
      <Column field="actorName" header="Actor name" />
      <Column field="resourceType" header="Resource type" />
      <Column field="resourceName" header="Resource name" />
      <Column field="nodePath" header="Node" />
    </DataTable>
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
    <Dropdown
      showClear
      loading={isPending}
      value={selectedItem}
      options={data?.map((item) => ({label: labelize(item), value: item}))}
      onChange={(e) => onChange({name, value: e.value})}
      placeholder={isPending ? "Loading..." : label}
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
  const [nodes, setNodes] = useState<TreeNode[]>([]);

  const logNodeToTreeNode = (node: LogNode): TreeNode => ({
    label: node.name,
    id: node.id,
    key: node.id,
    leaf: false
  });

  useEffect(() => {
    getAllLogNodes().then((nodes) => setNodes(nodes.map(logNodeToTreeNode)))
  }, []);

  const updateTreeNodeList = (nodes: TreeNode[], nodeToBeUpdated: TreeNode, func: (node: TreeNode) => TreeNode): TreeNode[] => {
    const updatedNodes: TreeNode[] = [];

    for (const node of nodes) {
      if (node.id === nodeToBeUpdated.id) {
        updatedNodes.push(func(nodeToBeUpdated));
      } else {
        updatedNodes.push({...node, children: node.children ? updateTreeNodeList(node.children, nodeToBeUpdated, func) : []});
      }
    }

    return updatedNodes;
  }

  const loadNodeChildren = async (e: TreeSelectEventNodeEvent) => {
    if (e.node.children !== undefined)
      return;
    const children = (await getAllLogNodes(e.node.id)).map(logNodeToTreeNode);
    setNodes(updateTreeNodeList(nodes, e.node, (node) => ({...node, children, expanded: true})));
  }

  const collapseNode = async (e: TreeSelectEventNodeEvent) => {
    setNodes(updateTreeNodeList(nodes, e.node, (node) => ({...node, expanded: false})));
  }

  return (
    <TreeSelect
      disabled={false}
      value={nodeId}
      options={nodes}
      onNodeSelect={(e) => {onChange({name: "nodeId", value: e.node.key?.toString()})}}
      onNodeExpand={loadNodeChildren}
      onNodeCollapse={collapseNode}
    />
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
    <div>
      <Button
        onClick={() => fetchNextPage()}
        disabled={!hasNextPage || isFetchingNextPage}
        icon={isFetchingNextPage ? "pi pi-spin pi-spinner" : null} label="Load more logs">
      </Button>
    </div>
  );

  return <LogTable logs={data.pages.flatMap((page) => page.logs)} footer={footer} />;
};

function LogFilters({onChange}: {onChange: (filter: LogFilterParams) => void}){
  const [params, setParams] = useState<LogFilterParams>({});

  const changeParam = ({name, value}: ValueChangeEvent) => {
    const update = {[name]: value};
    if (name === 'eventCategory')
      update['eventName'] = undefined;
    setParams({...params, ...update});
  }

  return (
    <div>
      {/* Event criteria */}
      <div className="flex flex-row py-5 space-x-5">
        <EventCategorySelector
          category={params.eventCategory}
          onChange={changeParam}/>
        <EventNameSelector
          name={params.eventName} category={params.eventCategory}
          onChange={changeParam}/>
      </div>

      {/* Actor criteria */}
      <div className="flex flex-row py-5 space-x-5">
        <ActorTypeSelector
          type={params.actorType}
          onChange={changeParam}/>
        <InputText
          placeholder="Actor name"
          value={params.actorName}
          onChange={(e) => changeParam({name: 'actorName', value: e.target.value})} />
      </div>

      {/* Resource criteria */}
      <div className="flex flex-row py-5 space-x-5">
        <ResourceTypeSelector
          type={params.resourceType}
          onChange={changeParam}/>
        <InputText
          placeholder="Resource name"
          value={params.resourceName}
          onChange={(e) => changeParam({name: 'resourceName', value: e.target.value})} />
      </div>

      {/* Tag criteria */}
      <div className="flex flex-row py-5 space-x-5">
        <TagCategorySelector
          category={params.tagCategory}
          onChange={changeParam}/>
        <InputText
          placeholder="Tag name"
          value={params.tagName}
          onChange={(e) => changeParam({name: 'tagName', value: e.target.value})} />
        <InputText
          placeholder="Tag id"
          value={params.tagId}
          onChange={(e) => changeParam({name: 'tagId', value: e.target.value})} />
      </div>

      {/* Node criteria */}
      <div className="flex flex-row py-5 space-x-5">
        <NodeSelector nodeId={params.nodeId || null} onChange={changeParam} />
      </div>

      {/* Apply button */}
      <Button
        onClick={() => onChange(params)}
        label="Apply filters"
      />
    </div>
  );
}

export default function LogList() {
  const [filter, setFilter] = useState<LogFilterParams>({});
  
  return (
    <div>
      <LogFilters onChange={setFilter} />
      <LogLoader filter={filter} />
    </div>
  );
}
