import { Button, Center } from "@mantine/core";
import { useInfiniteQuery, useQueryClient } from "@tanstack/react-query";
import deepEqual from "deep-equal";
import { useEffect, useRef } from "react";

import { getLogs, LogSearchParams, prepareLogSearchParamsForApi } from "../api";
import { LogTable, TableSearchParamChangeHandler } from "./LogTable";

export function LogLoader({
  searchParams,
  onTableSearchParamsChange,
  selectedColumns,
  onSelectedColumnsChange,
}: {
  searchParams: LogSearchParams;
  onTableSearchParamsChange: TableSearchParamChangeHandler;
  selectedColumns: string[];
  onSelectedColumnsChange: (selectedColumns: string[] | null) => void;
}) {
  const {
    isPending,
    error,
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteQuery({
    queryKey: ["logs", "list", prepareLogSearchParamsForApi(searchParams)],
    queryFn: async ({ pageParam }: { pageParam: string | null }) =>
      await getLogs(pageParam, searchParams),
    enabled: !!searchParams.repoId,
    initialPageParam: null,
    getNextPageParam: (lastPage) => lastPage.nextCursor,
  });
  const currentSearchParamsRef = useRef<LogSearchParams | null>(null);
  const queryClient = useQueryClient();

  // If the user apply search params A, then search params B, then search params A again,
  // he will see the logs of search params A with result pages already loaded, which can be confusing.
  // To avoid this, we remove the query for the previous search params when the user applies different search params.
  useEffect(() => {
    if (!deepEqual(searchParams, currentSearchParamsRef.current)) {
      queryClient.removeQueries({
        queryKey: ["logs", "list", currentSearchParamsRef.current],
      });
      currentSearchParamsRef.current = searchParams;
    }
  });

  // See comment above: we need to remove the result for the current search params when the component is unmounted,
  // because the useEffect above won't have a currentSearchParamsRef if the component is unmounted and remounted.
  useEffect(() => {
    return () =>
      queryClient.removeQueries({
        queryKey: ["logs", "list", currentSearchParamsRef.current],
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
      repoId={searchParams.repoId!}
      logs={data?.pages.flatMap((page) => page.logs)}
      isLoading={isPending || isFetchingNextPage}
      footer={footer}
      onTableSearchParamChange={onTableSearchParamsChange}
      selectedColumns={selectedColumns}
      onSelectedColumnsChange={onSelectedColumnsChange}
    />
  );
}
