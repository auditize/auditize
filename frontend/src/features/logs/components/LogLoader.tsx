import { Button, Center } from "@mantine/core";
import { useInfiniteQuery, useQueryClient } from "@tanstack/react-query";
import deepEqual from "deep-equal";
import { useEffect, useRef } from "react";

import { getLogs, LogSearchParams, prepareLogSearchParamsForApi } from "../api";
import { LogTable, TableFilterChangeHandler } from "./LogTable";

export function LogLoader({
  filter,
  onTableFilterChange,
}: {
  filter: LogSearchParams;
  onTableFilterChange: TableFilterChangeHandler;
}) {
  const {
    isPending,
    error,
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteQuery({
    queryKey: ["logs", "list", prepareLogSearchParamsForApi(filter)],
    queryFn: async ({ pageParam }: { pageParam: string | null }) =>
      await getLogs(pageParam, filter),
    enabled: !!filter.repoId,
    initialPageParam: null,
    getNextPageParam: (lastPage) => lastPage.nextCursor,
  });
  const currentFilterRef = useRef<LogSearchParams | null>(null);
  const queryClient = useQueryClient();

  // If the user apply filter A, then filter B, then filter A again, he will see the logs of filter A
  // with result pages already loaded, which can be confusing.
  // To avoid this, we remove the query for the previous filter when the user applies a different filter.
  useEffect(() => {
    if (!deepEqual(filter, currentFilterRef.current)) {
      queryClient.removeQueries({
        queryKey: ["logs", "list", currentFilterRef.current],
      });
      currentFilterRef.current = filter;
    }
  });

  // See comment above: we need to remove the result for the current filter when the component is unmounted,
  // because the useEffect above won't have a currentFilterRef if the component is unmounted and remounted.
  useEffect(() => {
    return () =>
      queryClient.removeQueries({
        queryKey: ["logs", "list", currentFilterRef.current],
      });
  }, []);

  if (error) return <div>Error: {error.message}</div>;

  const footer = (
    <Center>
      <Button
        onClick={() => fetchNextPage()}
        disabled={!hasNextPage || isFetchingNextPage}
        loading={isFetchingNextPage}
      >
        Load more
      </Button>
    </Center>
  );

  return (
    <LogTable
      repoId={filter.repoId!}
      logs={data?.pages.flatMap((page) => page.logs)}
      isLoading={isPending || isFetchingNextPage}
      footer={footer}
      onTableFilterChange={onTableFilterChange}
    />
  );
}
