import {
  PagePaginationInfo,
  reqGet,
  reqGetPaginated,
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

export async function createLogFilter(
  logFilter: LogFilterCreation,
): Promise<string> {
  const data = await reqPost("/users/me/logs/filters", logFilter);
  return data.id;
}

export async function getLogFilters(
  search: string | null = null,
  page = 1,
): Promise<[LogFilter[], PagePaginationInfo]> {
  return await reqGetPaginated("/users/me/logs/filters", { q: search, page });
}

export async function getLogFilter(logFilterId: string): Promise<LogFilter> {
  return await reqGet(`/users/me/logs/filters/${logFilterId}`);
}
