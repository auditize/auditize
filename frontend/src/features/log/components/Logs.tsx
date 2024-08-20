import { Flex, Stack } from "@mantine/core";
import { useDocumentTitle } from "@mantine/hooks";
import { useTranslation } from "react-i18next";

import Message from "@/components/Message";
import { useLogRepoListQuery } from "@/features/repo";

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
  const repoListQuery = useLogRepoListQuery({ enabled: withRepoSearchParam });
  const { searchParams, setSearchParams, selectedColumns, setSelectedColumns } =
    useLogNavigationState();
  useDocumentTitle(t("log.list.documentTitle"));

  if (repoListQuery.data && repoListQuery.data.length === 0) {
    return (
      <Flex justify="center">
        <Message.Warning textProps={{ size: "md" }}>
          {t("log.list.noRepos")}
        </Message.Warning>
      </Flex>
    );
  } else {
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
}
