import { Button, Center } from '@mantine/core';
import { useInfiniteQuery } from '@tanstack/react-query';
import { getLogs, LogsFilterParams } from '../api';
import { LogsTable } from './LogsTable';

export function LogsLoader(
  { filter = {}, onTableFilterChange } :
  { filter: LogsFilterParams; onTableFilterChange: (name: string, value: string) => void; }) {
  const { isPending, error, data, fetchNextPage, hasNextPage, isFetchingNextPage } = useInfiniteQuery({
    queryKey: ['logs', filter],
    queryFn: async ({ pageParam }: { pageParam: string | null; }) => await getLogs(pageParam, filter),
    enabled: !!filter.repoId,
    initialPageParam: null,
    getNextPageParam: (lastPage) => lastPage.nextCursor,
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
    <LogsTable
      repoId={filter.repoId!}
      logs={data.pages.flatMap((page) => page.logs)}
      footer={footer}
      onTableFilterChange={onTableFilterChange} />
  );
}
