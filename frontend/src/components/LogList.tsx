import {useState, useEffect} from 'react';

import { DataTable } from 'primereact/datatable';
import { Column } from 'primereact/column';
import { Button } from 'primereact/button';
import { useQuery } from '@tanstack/react-query';
import { labelize } from './utils';
import { LogService } from '../services/logs';


function mapLogToRow(log: Log): object {
  return {
    createdAt: log.saved_at,
    eventName: labelize(log.event.name),
    eventCategory: labelize(log.event.category),
    actorName: log.actor ? log.actor.name : null,
    resourceType: log.resource ? labelize(log.resource.type) : null,
    resourceName: log.resource ? log.resource.name : null,
    nodePath: log.node_path.map((n) => n.name).join(' > ')
  };
}

function mapLogsToRows(logs: Log[]): object[] {
  return logs.map(mapLogToRow);
}

export default function LogList() {
  const [service] = useState(() => new LogService());
  const [rows, setRows] = useState<Object[]>([]);
  const { isPending, error, data: logs } = useQuery({
    queryKey: ['logs'],
    queryFn: () => service.getLogs()
  });

  useEffect(() => {
    if (logs)
      setRows(mapLogsToRows(logs));
  }, [logs]);
  
  if (isPending)
    return <div>Loading...</div>;
  
  if (error)
    return <div>Error: {error.message}</div>;
  
  const loadMoreLogs = async () => {
    const newLogs = await service.getNextLogs();
    setRows([...rows, ...mapLogsToRows(newLogs)]);
  };

  const footer = <Button onClick={loadMoreLogs} plain>Load more logs</Button>;

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
};
