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
import { IconEdit, IconLogs, IconRestore, IconX } from "@tabler/icons-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import Message from "@/components/Message";
import { ScrollToTop } from "@/components/ScrollToTop";
import { LogFilterEdition, LogFilterFavoriteIcon } from "@/features/log-filter";
import { LogFilter, useLogFilterMutation } from "@/features/log-filter/api";
import { useLogRepoListQuery } from "@/features/repo";
import { iconBesideText } from "@/utils/ui";

import { LogSearchParams } from "../LogSearchParams";
import { LogNavigation, useLogNavigationState } from "./LogNavigation";
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
  const {
    searchParams,
    setSearchParams,
    selectedColumns,
    setSelectedColumns,
    logComponentRef,
  } = useLogNavigationState();

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
      <Stack ref={logComponentRef} gap="md">
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

function LogFilterEditAction({ filter }: { filter: LogFilter }) {
  const { t } = useTranslation();
  const [opened, setOpened] = useState(false);

  return (
    <>
      <Tooltip label={t("log.filter.edit.tooltip")} position="bottom" withArrow>
        <ActionIcon onClick={() => setOpened(true)} variant="default" size="md">
          <IconEdit style={{ width: rem(20) }} />
        </ActionIcon>
      </Tooltip>
      <LogFilterEdition
        filterId={opened ? filter.id : null}
        onClose={() => setOpened(false)}
      />
    </>
  );
}

function LogFilterRestoreAction({ filter }: { filter: LogFilter }) {
  const { t } = useTranslation();
  const navigate = useNavigate();

  return (
    <Tooltip label={t("log.filter.restore")} position="bottom">
      <ActionIcon
        onClick={() => navigate(`/logs?filterId=${filter.id}`)}
        variant="default"
        size="md"
      >
        <IconRestore style={{ width: rem(20) }} />
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

  useDocumentTitle(filter.name);

  return (
    <Group gap="lg">
      <span>
        <LogTitleIcon />
        {filter.name}
        {isDirty && (
          <Tooltip label={t("log.filter.dirty")} position="bottom">
            <span style={{ color: "var(--mantine-color-blue214-6)" }}>
              {" *"}
            </span>
          </Tooltip>
        )}
      </span>
      <ActionIcon.Group style={{ position: "relative", top: rem(1) }}>
        <LogFilterFavoriteAction filter={filter} />
        <LogFilterEditAction filter={filter} />
        {isDirty && <LogFilterRestoreAction filter={filter} />}
        <LogFilterClearAction />
      </ActionIcon.Group>
    </Group>
  );
}

function LogTitle() {
  const { t } = useTranslation();

  useDocumentTitle(t("log.list.documentTitle"));

  return (
    <>
      <LogTitleIcon />
      {t("log.logs")}
    </>
  );
}

export function Logs() {
  const { filter, isFilterDirty } = useLogNavigationState();

  return (
    <div>
      <Title order={1} pb="xl" fw={550} size="26">
        {filter ? (
          <LogFilterTitle filter={filter} isDirty={isFilterDirty!} />
        ) : (
          <LogTitle />
        )}
      </Title>
      <BaseLogs />
    </div>
  );
}
