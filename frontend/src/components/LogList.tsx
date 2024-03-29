import { useEffect, useState } from 'react';
import { DataTable } from 'primereact/datatable';
import { Column } from 'primereact/column';
import { Button } from 'primereact/button';
import { Dropdown } from 'primereact/dropdown';
import { InputText } from 'primereact/inputtext';
import { TreeNode } from 'primereact/treenode';
import { TreeSelect, TreeSelectEventNodeEvent, TreeSelectExpandedKeysType } from 'primereact/treeselect';
import { Tree } from 'primereact/tree';
import { useInfiniteQuery, useQuery } from '@tanstack/react-query';
import { labelize } from './utils';
import { timeout, getLogs, getAllLogEventNames, getAllLogEventCategories, getAllLogActorTypes, getAllLogResourceTypes, getAllLogTagCategories, getAllLogNodes, LogFilterParams } from '../services/logs';

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
  {name, queryKey, queryFn, selectedItem, onChange}:
  {name: string, queryKey: any, queryFn: () => Promise<string[]>, selectedItem?: string, onChange?: (name: string) => void}) {
  const {isPending, error, data} = useQuery({
    queryKey: queryKey,
    queryFn: queryFn
  });

  if (error)
    return <div>Error: {error.message}</div>;

  return (
    <Dropdown
      showClear
      loading={isPending}
      value={selectedItem}
      options={data?.map((item) => ({label: labelize(item), value: item}))}
      onChange={(e) => {
        console.log("onChange", e.value);
        onChange?.(e.value);
      }}
      placeholder={isPending ? "Loading..." : name}
    />
  );
}

function EventCategorySelector({category, onChange}: {category?: string, onChange?: (category: string) => void}) {
  return (
    <PaginatedSelector
      name="Event category"
      queryKey={['logEventCategory']} queryFn={getAllLogEventCategories}
      selectedItem={category} onChange={onChange} />
  );
}

function EventNameSelector(
  {name, category, onChange}: {name?: string, category?: string, onChange?: (name: string) => void}) {
  return (
    <PaginatedSelector
      name="Event name"
      queryKey={['logEventNames', category]} queryFn={() => getAllLogEventNames(category)}
      selectedItem={name} onChange={onChange} />
  );
}

function ActorTypeSelector({type, onChange}: {type?: string, onChange?: (type: string) => void}) {
  return (
    <PaginatedSelector
      name="Actor type"
      queryKey={['logActorType']} queryFn={getAllLogActorTypes}
      selectedItem={type} onChange={onChange} />
  );
}

function ResourceTypeSelector({type, onChange}: {type?: string, onChange?: (type: string) => void}) {
  return (
    <PaginatedSelector
      name="Resource type"
      queryKey={['logResourceType']} queryFn={getAllLogResourceTypes}
      selectedItem={type} onChange={onChange} />
  );
}

function TagCategorySelector({category, onChange}: {category?: string, onChange?: (category: string) => void}) {
  return (
    <PaginatedSelector
      name="Tag category"
      queryKey={['logTagCategory']} queryFn={getAllLogTagCategories}
      selectedItem={category} onChange={onChange} />
  );
}

function NodeSelector({nodeId, onChange}: {nodeId: string | null, onChange: (nodeId: string | null) => void}) {
  const [nodes, setNodes] = useState<TreeNode[]>([]);

  const logNodeToTreeNode = (node: LogNode): TreeNode => ({
    label: node.name,
    id: node.id,
    key: node.id,
    children: [],
    leaf: false
  });

  useEffect(() => {
    getAllLogNodes().then((nodes) => setNodes(nodes.map(logNodeToTreeNode)))
  }, []);

  const updateTreeNodeList = (nodes: TreeNode[], nodeToBeUpdated: TreeNode, children: TreeNode[]): TreeNode[] => {
    const updatedNodes: TreeNode[] = [];

    for (const node of nodes) {
      if (node.id === nodeToBeUpdated.id) {
        updatedNodes.push({...nodeToBeUpdated, children, expanded: true});
      } else {
        updatedNodes.push({...node, children: node.children ? updateTreeNodeList(node.children, nodeToBeUpdated, children) : []});
      }
    }

    return updatedNodes;
  }

  const loadNodeChildren = async (e: TreeSelectEventNodeEvent) => {
    const children = (await getAllLogNodes(e.node.id)).map(logNodeToTreeNode);
    setNodes(updateTreeNodeList(nodes, e.node, children));
  }

  return (
    <TreeSelect
      disabled={false}
      value={nodeId}
      options={nodes}
      onNodeSelect={(e) => {onChange(e.node.key?.toString() || null)}}
      onNodeExpand={loadNodeChildren}
    />
  );
}

function LogLoader({filter = {}}: {filter: LogFilterParams}) {
  const { isPending, error, data, fetchNextPage, hasNextPage, isFetchingNextPage } = useInfiniteQuery({
    queryKey: ['logs', filter],
    queryFn: async ({ pageParam }: {pageParam: string | null}) => await getLogs(pageParam, filter),
    initialPageParam: null,
    getNextPageParam: (lastPage) => lastPage.nextCursor
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
  const [eventName, setEventName] = useState<string>();
  const [eventCategory, setEventCategory] = useState<string>();
  const [actorType, setActorType] = useState<string>();
  const [actorName, setActorName] = useState<string>("");
  const [resourceType, setResourceType] = useState<string>();
  const [resourceName, setResourceName] = useState<string>("");
  const [tagCategory, setTagCategory] = useState<string>();
  const [tagName, setTagName] = useState<string>("");
  const [tagId, setTagId] = useState<string>();
  const [nodeId, setNodeId] = useState<string | null>(null);

  return (
    <div>
      {/* Event criteria */}
      <div className="flex flex-row py-5 space-x-5">
        <EventCategorySelector
          category={eventCategory}
          onChange={(category) => {
            setEventCategory(category);
            setEventName(undefined);
          }}/>
        <EventNameSelector
          name={eventName} category={eventCategory}
          onChange={setEventName}/>
      </div>

      {/* Actor criteria */}
      <div className="flex flex-row py-5 space-x-5">
        <ActorTypeSelector
          type={actorType}
          onChange={setActorType}/>
        <InputText placeholder="Actor name" value={actorName} onChange={(e) => setActorName(e.target.value)} />
      </div>

      {/* Resource criteria */}
      <div className="flex flex-row py-5 space-x-5">
      <ResourceTypeSelector
          type={resourceType}
          onChange={setResourceType}/>
        <InputText placeholder="Resource name" value={resourceName} onChange={(e) => setResourceName(e.target.value)} />
      </div>

      {/* Tag criteria */}
      <div className="flex flex-row py-5 space-x-5">
        <TagCategorySelector
          category={tagCategory}
          onChange={setTagCategory}/>
        <InputText placeholder="Tag name" value={tagName} onChange={(e) => setTagName(e.target.value)} />
        <InputText placeholder="Tag id" value={tagId} onChange={(e) => setTagId(e.target.value)} />
      </div>

      {/* Node criteria */}
      <div className="flex flex-row py-5 space-x-5">
        <NodeSelector nodeId={nodeId} onChange={setNodeId} />
      </div>

      {/* Apply button */}
      <Button
        onClick={() => onChange({
          eventCategory, eventName,
          actorType, actorName,
          resourceType, resourceName,
          tagCategory, tagName, tagId,
          nodeId: nodeId || undefined
        })}
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
