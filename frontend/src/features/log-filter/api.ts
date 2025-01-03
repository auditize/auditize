import { useMutation, useQueryClient } from "@tanstack/react-query";

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
  isFavorite: boolean;
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
  isFavorite?: boolean;
}

export async function createLogFilter(
  logFilter: LogFilterCreation,
): Promise<string> {
  const data = await reqPost("/users/me/logs/filters", logFilter);
  return data.id;
}

export async function getLogFilters({
  search = null,
  isFavorite,
  page = 1,
  pageSize = 10,
}: {
  search?: string | null;
  isFavorite?: boolean;
  page?: number;
  pageSize?: number;
} = {}): Promise<[LogFilter[], PagePaginationInfo]> {
  return await reqGetPaginated("/users/me/logs/filters", {
    q: search,
    isFavorite,
    page,
    pageSize,
  });
}

export async function getLogFilter(logFilterId: string): Promise<LogFilter> {
  return await reqGet(`/users/me/logs/filters/${logFilterId}`);
}

export async function updateLogFilter(
  id: string,
  update: LogFilterUpdate,
): Promise<void> {
  await reqPatch(`/users/me/logs/filters/${id}`, update);
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
        queryKey: ["logFilters"],
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
