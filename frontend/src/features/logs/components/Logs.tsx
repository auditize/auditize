import { Stack } from "@mantine/core";
import { useDocumentTitle, useLocalStorage } from "@mantine/hooks";
import { useTranslation } from "react-i18next";

import { buildLogSearchParams } from "../api";
import { useLogContext } from "../context";
import { LogFilter } from "./LogFilter";
import { LogLoader } from "./LogLoader";

const DEFAULT_COLUMNS = ["date", "actor", "action", "resource", "node", "tag"];

export function Logs({ withRepoFilter = true }: { withRepoFilter?: boolean }) {
  const { t } = useTranslation();
  const { filter, setFilter } = useLogContext();
  const [selectedColumns, setSelectedColumns] = useLocalStorage<
    Record<string, string[]>
  >({
    key: `log-columns`,
    defaultValue: {},
  });
  useDocumentTitle(t("log.list.documentTitle"));

  return (
    <Stack gap="lg" pt="xs">
      <LogFilter
        params={filter}
        onChange={(newFilter) => {
          setFilter(newFilter);
        }}
        withRepoFilter={withRepoFilter}
      />
      <LogLoader
        filter={filter}
        onTableFilterChange={(name, value) => {
          setFilter({
            ...buildLogSearchParams(),
            repoId: filter.repoId,
            since: filter.since,
            until: filter.until,
            [name]: value,
          });
        }}
        selectedColumns={selectedColumns[filter.repoId] ?? DEFAULT_COLUMNS}
        onSelectedColumnsChange={(repoSelectedColumns) =>
          setSelectedColumns((selectedColumns) => ({
            ...selectedColumns,
            [filter.repoId]: repoSelectedColumns
              ? repoSelectedColumns
              : DEFAULT_COLUMNS,
          }))
        }
      />
    </Stack>
  );
}
