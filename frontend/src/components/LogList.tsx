import {useState, useEffect} from 'react';

import { DataTable } from 'primereact/datatable';
import { Column } from 'primereact/column';
import { Button } from 'primereact/button';
import { useQuery } from '@tanstack/react-query';
import { labelize } from './utils';
import { getLogs } from '../services/logs';

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

export default function LogList() {
  const [cursor, setCursor] = useState<string | null>(null);
  const { isPending, error, data } = useQuery({
    queryKey: ['logs', cursor],
    queryFn: () => getLogs(cursor)
  });
  const [allLogs, setAllLogs] = useState<Log[]>([]);

  useEffect(() => {
    if (data) {
      const {logs} = data;
      setAllLogs(prevLogs => [...prevLogs, ...logs]);
    }
  }, [data?.nextCursor]);

  if (isPending)
    return <div>Loading...</div>;
  
  if (error)
    return <div>Error: {error.message}</div>;

  const { nextCursor } = data; 
    
  const footer = (
    <div>
      <Button onClick={() => setCursor(nextCursor)} disabled={nextCursor === null}>
        Load more logs
      </Button>
    </div>
  );

  return <LogTable logs={allLogs} footer={footer} />;
};
