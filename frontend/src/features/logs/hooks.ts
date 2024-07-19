import { useLocalStorage } from "@mantine/hooks";

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
