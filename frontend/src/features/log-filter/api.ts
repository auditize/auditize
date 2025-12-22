import { useMutation, useQueryClient } from "@tanstack/react-query";

import {
  PagePaginationInfo,
  reqDelete,
  reqGet,
  reqGetPaginated,
  reqPatch,
  reqPost,
} from "@/utils/api";
import {
  snakeCaseToCamelCaseObjectKeys,
  snakeCaseToCamelCaseString,
} from "@/utils/switchCase";

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

function normalizeLogFilter(data: any): LogFilter {
  // the searchParams is an object that can contain custom field parameter names with
  // underscore that must be preserved, that's why we do a manual case conversion
  const filter: LogFilter = snakeCaseToCamelCaseObjectKeys(data, 1);
  filter.searchParams = Object.fromEntries(
    Object.entries(filter.searchParams).map(([key, value]) => [
      key.match(/^(source|resource|details|actor)\./)
        ? key
        : snakeCaseToCamelCaseString(key),
      value,
    ]),
  );
  return filter;
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
  const [items, pagination] = await reqGetPaginated(
    "/users/me/logs/filters",
    {
      q: search,
      is_favorite: isFavorite,
      page,
      page_size: pageSize,
    },
    { raw: true },
  );
  // see getLogFilter for more details on the manual case conversion
  const normalizedItems = items.map(normalizeLogFilter);
  return [normalizedItems, pagination];
}

export async function getLogFilter(logFilterId: string): Promise<LogFilter> {
  const data = await reqGet(
    `/users/me/logs/filters/${logFilterId}`,
    {},
    { raw: true },
  );

  return normalizeLogFilter(data);
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
