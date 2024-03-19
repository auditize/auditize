
import { DataTable } from 'primereact/datatable';
import { Column } from 'primereact/column';
import { useQuery } from '@tanstack/react-query';
import { getLogs } from '../services/logs';
import { labelize } from './utils';

export default function LogList() {
  const { isPending, error, data: logs } = useQuery({
    queryKey: ['logs'],
    queryFn: () => getLogs()
  });

  let rows = [];

  if (isPending)
    return <div>Loading...</div>;
  
  if (error)
    return <div>Error: {error.message}</div>;
  
  rows = logs.map((log: Log) => ({
    createdAt: log.saved_at,
    eventName: labelize(log.event.name),
    eventCategory: labelize(log.event.category),
    actorName: log.actor ? log.actor.name : null,
    resourceType: log.resource ? labelize(log.resource.type) : null,
    resourceName: log.resource ? log.resource.name : null,
    nodePath: log.node_path.map((n) => n.name).join(' > ')
  }));

  return (
    <DataTable value={rows} size="small" showGridlines>
      <Column field="createdAt" header="Date" />
      <Column field="eventCategory" header="Event category" />
      <Column field="eventName" header="Event name" />
      <Column field="actorName" header="Actor name" />
      <Column field="resourceType" header="Resource type" />
      <Column field="resourceName" header="Resource name" />
      <Column field="nodePath" header="Node" />
    </DataTable>
  );
};
