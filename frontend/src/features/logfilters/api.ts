import { reqPost } from "@/utils/api";

export interface LogFilterCreation {
  name: string;
  repoId: string;
  searchParams: Record<string, string>;
  columns: string[];
}

export async function createLogFilter(
  logFilter: LogFilterCreation,
): Promise<string> {
  const data = await reqPost("/users/me/logs/filters", logFilter);
  return data.id;
}
