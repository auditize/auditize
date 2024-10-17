import { Flex, Stack, Title } from "@mantine/core";
import { useDocumentTitle } from "@mantine/hooks";
import { IconLogs } from "@tabler/icons-react";
import { useTranslation } from "react-i18next";

import Message from "@/components/Message";
import { ScrollToTop } from "@/components/ScrollToTop";
import { useLogRepoListQuery } from "@/features/repo";
import { iconBesideText } from "@/utils/ui";

import { LogSearchParams } from "../LogSearchParams";
import { LogNavigation } from "./LogNavigation";
import { useLogNavigationState } from "./LogNavigationState";
import { LogTable } from "./LogTable";

export function BaseLogs({
  withRepoSearchParam = true,
  withLogFilters = true,
  withScrollToTop = true,
}: {
  withRepoSearchParam?: boolean;
  withLogFilters?: boolean;
  withScrollToTop?: boolean;
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
      <Stack gap="md">
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
        {withScrollToTop && <ScrollToTop />}
      </Stack>
    );
  }
}

export function Logs() {
  const { t } = useTranslation();
  const { filterName } = useLogNavigationState();

  return (
    <div>
      <Title order={1} pb="xl" fw={550} size="26">
        <IconLogs
          style={iconBesideText({
            size: "26",
            top: "4px",
            marginRight: "0.25rem",
          })}
        />
        {filterName ? filterName : t("log.logs")}
      </Title>
      <BaseLogs />
    </div>
  );
}
