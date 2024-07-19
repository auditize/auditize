import { Stack } from "@mantine/core";
import { useDocumentTitle, useLocalStorage } from "@mantine/hooks";
import { useTranslation } from "react-i18next";

import { buildLogSearchParams } from "../api";
import { useLogContext } from "../context";
import { useLogSelectedColumns } from "../hooks";
import { LogLoader } from "./LogLoader";
import { LogNavigation } from "./LogNavigation";

export function Logs({
  withRepoSearchParam = true,
}: {
  withRepoSearchParam?: boolean;
}) {
  const { t } = useTranslation();
  const { searchParams, setSearchParams } = useLogContext();
  const [selectedColumns, setSelectedColumns] = useLogSelectedColumns(
    searchParams.repoId,
  );
  useDocumentTitle(t("log.list.documentTitle"));

  return (
    <Stack gap="lg" pt="xs">
      <LogNavigation
        params={searchParams}
        onChange={(newSearchParams) => {
          setSearchParams(newSearchParams);
        }}
        selectedColumns={selectedColumns}
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
        selectedColumns={selectedColumns}
        onSelectedColumnsChange={setSelectedColumns}
      />
    </Stack>
  );
}
