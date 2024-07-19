import { useLocalStorage } from "@mantine/hooks";
import { useQuery } from "@tanstack/react-query";

import { getAllMyRepos, UserRepo } from "../repos/api";

const DEFAULT_COLUMNS = ["date", "actor", "action", "resource", "node", "tag"];

export function useLogSelectedColumns(
  repoId: string,
): [string[], (columns: string[] | null) => void] {
  const [perRepoColumns, setPerRepoColumns] = useLocalStorage<
    Record<string, string[]>
  >({
    key: `auditize-log-columns`,
    defaultValue: {},
  });
  return [
    perRepoColumns[repoId] ?? DEFAULT_COLUMNS,
    (columns) =>
      setPerRepoColumns((perRepoColumns) => ({
        ...perRepoColumns,
        [repoId]: columns ? columns : DEFAULT_COLUMNS,
      })),
  ];
}

export function useLogRepoQuery() {
  return useQuery({
    queryKey: ["myLogRepos"],
    queryFn: () => getAllMyRepos({ hasReadPermission: true }),
  });
}
