import { ActionIcon, Menu, Tooltip } from "@mantine/core";
import {
  IconAdjustmentsHorizontal,
  IconDeviceFloppy,
  IconDots,
  IconDownload,
  IconFilter,
} from "@tabler/icons-react";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { NavLink, useNavigate } from "react-router-dom";

import { notifyError, notifySuccess } from "@/components/notifications";
import {
  getLogFilters,
  LogFilterCreation,
  LogFilterDrawer,
  normalizeFilterColumnsForApi,
  useLogFilterMutation,
} from "@/features/log-filter";
import { sortLogFields } from "@/features/log/components/LogTable";
import { LogSearchParams } from "@/features/log/LogSearchParams";
import { camelCaseToSnakeCaseString } from "@/utils/switchCase";
import { iconSize } from "@/utils/ui";

import { useLogNavigationState } from "./LogNavigationState";

function columnsToCsvColumns(columns: string[]): string[] {
  return Array.from(
    // If the user has also selected a field like "action_type", "action_category" etc..,
    // we use a Set to avoid duplicates
    new Set(
      columns
        .toSorted(sortLogFields)
        .map((column) => {
          if (column === "actor") {
            return ["actor_name"];
          }
          if (column === "action") {
            return ["action_type", "action_category"];
          }
          if (column === "resource") {
            return ["resource_type", "resource_name"];
          }
          if (column === "entity") {
            return ["entity_path:name"];
          }
          if (column === "tag") {
            return ["tag_type"];
          }
          if (column === "attachment") {
            return ["attachment_name"];
          }
          return [camelCaseToSnakeCaseString(column)];
        })
        .flat(),
    ),
  );
}

function ExtraActionsExport({
  searchParams,
  selectedColumns,
}: {
  searchParams: LogSearchParams;
  selectedColumns: string[];
}) {
  const { t } = useTranslation();
  const csvExportUrl =
    (window.auditizeBaseURL ?? "") +
    "/api/repos/" +
    searchParams.repoId +
    "/logs/csv?" +
    new URLSearchParams(
      searchParams.serialize({
        includeRepoId: false,
        snakeCase: true,
      }),
    ).toString();
  const jsonlExportUrl =
    (window.auditizeBaseURL ?? "") +
    "/api/repos/" +
    searchParams.repoId +
    "/logs/jsonl?" +
    new URLSearchParams(
      searchParams.serialize({ includeRepoId: false, snakeCase: true }),
    ).toString();

  return (
    <>
      <Menu.Label>{t("log.export.export")}</Menu.Label>
      <Menu.Item
        component="a"
        href={csvExportUrl}
        leftSection={<IconDownload style={iconSize(14)} />}
      >
        {t("log.export.csvExportDefault")}
      </Menu.Item>
      <Menu.Item
        component="a"
        href={`${csvExportUrl}&columns=${columnsToCsvColumns(selectedColumns).join(",")}`}
        leftSection={<IconDownload style={iconSize(14)} />}
      >
        {t("log.export.csvExportCurrent")}
      </Menu.Item>
      <Menu.Item
        component="a"
        href={jsonlExportUrl}
        leftSection={<IconDownload style={iconSize(14)} />}
      >
        {t("log.export.jsonlExport")}
      </Menu.Item>
    </>
  );
}

function useFavoriteLogFiltersQuery(enabled = true) {
  return useQuery({
    queryKey: ["logFilters", { isFavorite: true }],
    queryFn: () =>
      getLogFilters({ isFavorite: true, pageSize: 10 }).then(
        ([filters]) => filters,
      ),
    enabled: enabled,
  });
}

function ExtraActionsFavoriteFilters() {
  const { t } = useTranslation();
  const filtersQuery = useFavoriteLogFiltersQuery();
  const filters = filtersQuery.data;

  return (
    filters &&
    filters.length > 0 && (
      <>
        <Menu.Divider />
        <Menu.Label>{t("log.filter.favoriteFilters")}</Menu.Label>
        {filters.map((filter) => (
          <Menu.Item
            key={filter.id}
            component={NavLink}
            to={`/logs?filterId=${filter.id}`}
            leftSection={<IconFilter style={iconSize(14)} />}
          >
            {filter.name}
          </Menu.Item>
        ))}
      </>
    )
  );
}

function ExtraActionsFilterManagement({
  searchParams,
  openFilterCreation,
  openFilterManagement,
}: {
  searchParams: LogSearchParams;
  openFilterCreation: () => void;
  openFilterManagement: () => void;
}) {
  const { t } = useTranslation();
  const { filter, isFilterDirty } = useLogNavigationState();
  const navigate = useNavigate();
  const mutation = useLogFilterMutation(filter?.id!, {
    onSuccess: () => {
      notifySuccess(t("log.filter.updateSuccess"));
      navigate(`/logs?filterId=${filter?.id!}`);
    },
    onError: () => {
      notifyError(t("log.filter.updateError"));
    },
  });

  return (
    <>
      <Menu.Divider />
      <Menu.Label>{t("log.filter.filters")}</Menu.Label>
      {filter && isFilterDirty && (
        <Menu.Item
          component="a"
          onClick={() =>
            mutation.mutate({
              searchParams: searchParams.serialize({
                includeRepoId: false,
                snakeCase: true,
              }),
            })
          }
          leftSection={<IconDeviceFloppy style={iconSize(14)} />}
        >
          {t("log.filter.saveChanges")}
        </Menu.Item>
      )}
      <Menu.Item
        component="a"
        onClick={openFilterCreation}
        leftSection={<IconDeviceFloppy style={iconSize(14)} />}
      >
        {t(filter ? "log.filter.saveAsNew" : "log.filter.save")}
      </Menu.Item>
      <Menu.Item
        component="a"
        onClick={openFilterManagement}
        leftSection={<IconAdjustmentsHorizontal style={iconSize(14)} />}
      >
        {t("log.filter.manage")}
      </Menu.Item>
    </>
  );
}

export function ExtraActions({
  searchParams,
  selectedColumns,
  withLogFilters,
}: {
  searchParams: LogSearchParams;
  selectedColumns: string[];
  withLogFilters: boolean;
}) {
  const { t } = useTranslation();
  const [menuOpened, setMenuOpened] = useState(false);
  const [filterCreationOpened, setFilterCreationOpened] = useState(false);
  const [filterManagementOpened, setFilterManagementOpened] = useState(false);
  useFavoriteLogFiltersQuery(withLogFilters); // prefetch favorite filters

  return (
    <>
      {withLogFilters && (
        <>
          <LogFilterCreation
            repoId={searchParams.repoId}
            searchParams={searchParams.serialize({
              includeRepoId: false,
              snakeCase: true,
            })}
            columns={normalizeFilterColumnsForApi(selectedColumns)}
            opened={filterCreationOpened}
            onClose={() => setFilterCreationOpened(false)}
          />
          <LogFilterDrawer
            opened={filterManagementOpened}
            onClose={() => setFilterManagementOpened(false)}
          />
        </>
      )}
      <Menu
        opened={menuOpened}
        onChange={setMenuOpened}
        shadow="md"
        withinPortal={false}
      >
        <Menu.Target>
          <Tooltip
            label={t("log.moreActions")}
            disabled={menuOpened}
            position="bottom-end"
            withArrow
            withinPortal={false}
          >
            <ActionIcon size="input-sm">
              <IconDots />
            </ActionIcon>
          </Tooltip>
        </Menu.Target>
        <Menu.Dropdown>
          <ExtraActionsExport
            searchParams={searchParams}
            selectedColumns={selectedColumns}
          />
          {withLogFilters && (
            <>
              <ExtraActionsFavoriteFilters />
              <ExtraActionsFilterManagement
                searchParams={searchParams}
                openFilterManagement={() => setFilterManagementOpened(true)}
                openFilterCreation={() => setFilterCreationOpened(true)}
              />
            </>
          )}
        </Menu.Dropdown>
      </Menu>
    </>
  );
}
