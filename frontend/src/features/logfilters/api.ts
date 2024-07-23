import { useMutation, useQueryClient } from "@tanstack/react-query";
import camelcaseKeys from "camelcase-keys";

import {
  PagePaginationInfo,
  reqDelete,
  reqGet,
  reqGetPaginated,
  reqPatch,
  reqPost,
} from "@/utils/api";

export interface LogFilterCreation {
  name: string;
  repoId: string;
  searchParams: Record<string, string>;
  columns: string[];
}

export interface LogFilter extends LogFilterCreation {
  id: string;
  createdAt: string;
}

export interface LogFilterUpdate {
  name?: string;
  repoId?: string;
  searchParams?: Record<string, string>;
  columns?: string[];
}

export async function createLogFilter(
  logFilter: LogFilterCreation,
): Promise<string> {
  const data = await reqPost(
    "/users/me/logs/filters",
    {
      name: logFilter.name,
      repo_id: logFilter.repoId,
      search_params: logFilter.searchParams,
      columns: logFilter.columns,
    },
    { disableBodySnakecase: true },
  );
  return data.id;
}

export async function getLogFilters(
  search: string | null = null,
  page = 1,
): Promise<[LogFilter[], PagePaginationInfo]> {
  const [filters, pagination] = await reqGetPaginated(
    "/users/me/logs/filters",
    { q: search, page },
    { disableResponseCamelcase: true },
  );
  return [
    camelcaseKeys(filters, { deep: true, exclude: [/.*\..*/] }),
    pagination,
  ];
}

export async function getLogFilter(logFilterId: string): Promise<LogFilter> {
  const filter = await reqGet(
    `/users/me/logs/filters/${logFilterId}`,
    undefined,
    { disableResponseCamelcase: true },
  );
  return camelcaseKeys(filter, { deep: true, exclude: [/.*\..*/] });
}

export async function updateLogFilter(
  id: string,
  update: LogFilterUpdate,
): Promise<void> {
  await reqPatch(
    `/users/me/logs/filters/${id}`,
    {
      name: update.name,
      repo_id: update.repoId,
      search_params: update.searchParams,
      columns: update.columns,
    },
    { disableBodySnakecase: true },
  );
}

export function useLogFilterMutation(
  id: string,
  {
    onSuccess,
    onError,
  }: { onSuccess?: () => void; onError?: (error: Error) => void } = {},
) {
  const queryClient = useQueryClient();
  const filterMutation = useMutation({
    mutationFn: (params: LogFilterUpdate) => updateLogFilter(id, params),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["logFilter", id],
      });
      if (onSuccess) {
        onSuccess();
      }
    },
    onError,
  });
  return filterMutation;
}

export async function deleteLogFilter(filterId: string): Promise<void> {
  await reqDelete("/users/me/logs/filters/" + filterId);
}
