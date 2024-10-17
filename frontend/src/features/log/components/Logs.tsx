import {
  ActionIcon,
  Flex,
  Group,
  rem,
  Stack,
  Title,
  Tooltip,
} from "@mantine/core";
import { useDocumentTitle } from "@mantine/hooks";
import { IconLogs, IconX } from "@tabler/icons-react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import Message from "@/components/Message";
import { ScrollToTop } from "@/components/ScrollToTop";
import { LogFilterFavoriteIcon } from "@/features/log-filter";
import { LogFilter, useLogFilterMutation } from "@/features/log-filter/api";
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

function LogFilterFavoriteAction({ filter }: { filter: LogFilter }) {
  const { t } = useTranslation();
  const filterMutation = useLogFilterMutation(filter.id);

  return (
    <Tooltip
      label={
        filter.isFavorite
          ? t("log.filter.unsetFavorite")
          : t("log.filter.setFavorite")
      }
      position="bottom"
      withArrow
    >
      <ActionIcon
        onClick={() =>
          filterMutation.mutate({ isFavorite: !filter.isFavorite })
        }
        loading={filterMutation.isPending}
        loaderProps={{ type: "dots" }}
        variant="default"
        size="md"
      >
        <LogFilterFavoriteIcon
          value={filter.isFavorite}
          style={{ width: rem(20) }}
        />
      </ActionIcon>
    </Tooltip>
  );
}

function LogFilterClearAction() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { searchParams } = useLogNavigationState();

  return (
    <Tooltip label={t("log.filter.clear")} position="bottom">
      <ActionIcon
        onClick={() => navigate(`/logs?repoId=${searchParams.repoId}`)}
        variant="default"
        size="md"
      >
        <IconX style={{ width: rem(20) }} />
      </ActionIcon>
    </Tooltip>
  );
}

function LogTitleIcon() {
  return (
    <IconLogs
      style={iconBesideText({
        size: "26",
        top: "4px",
        marginRight: "0.25rem",
      })}
    />
  );
}

function LogFilterTitle({
  filter,
  isDirty,
}: {
  filter: LogFilter;
  isDirty: boolean;
}) {
  const { t } = useTranslation();

  return (
    <Group gap="lg">
      <span>
        <LogTitleIcon />
        {filter.name}
        {isDirty ? (
          <Tooltip label={t("log.filter.dirty")} position="bottom">
            <span style={{ color: "var(--mantine-color-blue214-6)" }}>
              {" *"}
            </span>
          </Tooltip>
        ) : undefined}
      </span>
      <ActionIcon.Group style={{ position: "relative", top: rem(2) }}>
        <LogFilterFavoriteAction filter={filter} />
        <LogFilterClearAction />
      </ActionIcon.Group>
    </Group>
  );
}

export function Logs() {
  const { t } = useTranslation();
  const { filter, isFilterDirty } = useLogNavigationState();

  return (
    <div>
      <Title order={1} pb="xl" fw={550} size="26">
        {filter ? (
          <LogFilterTitle filter={filter} isDirty={isFilterDirty!} />
        ) : (
          <>
            <LogTitleIcon />
            {t("log.logs")}
          </>
        )}
      </Title>
      <BaseLogs />
    </div>
  );
}
