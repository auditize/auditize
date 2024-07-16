import { Stack } from "@mantine/core";
import { useDocumentTitle, useLocalStorage } from "@mantine/hooks";
import { useTranslation } from "react-i18next";

import { buildLogSearchParams } from "../api";
import { useLogContext } from "../context";
import { LogLoader } from "./LogLoader";
import { LogNavigation } from "./LogNavigation";

const DEFAULT_COLUMNS = ["date", "actor", "action", "resource", "node", "tag"];

export function Logs({
  withRepoSearchParam = true,
}: {
  withRepoSearchParam?: boolean;
}) {
  const { t } = useTranslation();
  const { searchParams, setSearchParams } = useLogContext();
  const [selectedColumns, setSelectedColumns] = useLocalStorage<
    Record<string, string[]>
  >({
    key: `log-columns`,
    defaultValue: {},
  });
  const repoSelectedColumns =
    selectedColumns[searchParams.repoId] ?? DEFAULT_COLUMNS;
  useDocumentTitle(t("log.list.documentTitle"));

  return (
    <Stack gap="lg" pt="xs">
      <LogNavigation
        params={searchParams}
        onChange={(newSearchParams) => {
          setSearchParams(newSearchParams);
        }}
        selectedColumns={repoSelectedColumns}
        withRepoSearchParam={withRepoSearchParam}
      />
      <LogLoader
        searchParams={searchParams}
        onTableSearchParamsChange={(name, value) => {
          setSearchParams({
            ...buildLogSearchParams(),
            repoId: searchParams.repoId,
            since: searchParams.since,
            until: searchParams.until,
            [name]: value,
          });
        }}
        selectedColumns={repoSelectedColumns}
        onSelectedColumnsChange={(repoSelectedColumns) =>
          setSelectedColumns((selectedColumns) => ({
            ...selectedColumns,
            [searchParams.repoId]: repoSelectedColumns
              ? repoSelectedColumns
              : DEFAULT_COLUMNS,
          }))
        }
      />
    </Stack>
  );
}
