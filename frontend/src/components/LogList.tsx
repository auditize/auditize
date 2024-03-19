
import { DataTable } from 'primereact/datatable';
import { Column } from 'primereact/column';
import { useQuery } from '@tanstack/react-query';
import { getLogs } from '../services/logs';

export default function LogList() {
  const { isPending, error, data: logs } = useQuery({
    queryKey: ['logs'],
    queryFn: () => getLogs()
  });

  let rows = [];

  if (isPending) {
    return <div>Loading...</div>;
  } else if (error) {
    return <div>Error: {error.message}</div>;
  } else {
    rows = logs.map((log: Log) => ({
        createdAt: log.saved_at,
        eventName: log.event.name,
        eventCategory: log.event.category
    }));
  }

  // const logs = [
  //   { id: 1, name: 'Log 1', description: 'Description 1' },
  //   { id: 2, name: 'Log 2', description: 'Description 2' },
  //   { id: 3, name: 'Log 3', description: 'Description 3' },
  // ];

  return (
    <DataTable value={rows}>
      <Column field="createdAt" header="Date" />
      <Column field="eventCategory" header="Event category" />
      <Column field="eventName" header="Event name" />
    </DataTable>
  );
};
