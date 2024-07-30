import { Stack } from "@mantine/core";
import { useDocumentTitle } from "@mantine/hooks";
import { useTranslation } from "react-i18next";

import { LogSearchParams } from "../LogSearchParams";
import { LogNavigation } from "./LogNavigation";
import { useLogNavigationState } from "./LogNavigationState";
import { LogTable } from "./LogTable";

export function Logs({
  withRepoSearchParam = true,
  withLogFilters = true,
}: {
  withRepoSearchParam?: boolean;
  withLogFilters?: boolean;
}) {
  const { t } = useTranslation();
  const { searchParams, setSearchParams, selectedColumns, setSelectedColumns } =
    useLogNavigationState();
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
        withLogFilters={withLogFilters}
      />
      <LogTable
        searchParams={searchParams}
        onTableSearchParamChange={(name, value) => {
          setSearchParams(
            LogSearchParams.fromProperties({
              repoId: searchParams.repoId,
              since: searchParams.since,
              until: searchParams.until,
              [name]: value,
            }),
          );
        }}
        selectedColumns={selectedColumns}
        onSelectedColumnsChange={setSelectedColumns}
      />
    </Stack>
  );
}
