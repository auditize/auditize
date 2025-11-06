import { ActionIcon, Button, Group, Menu, rem, Tooltip } from "@mantine/core";
import {
  IconAdjustmentsHorizontal,
  IconDeviceFloppy,
  IconDots,
  IconDownload,
  IconFilter,
} from "@tabler/icons-react";
import { useQuery } from "@tanstack/react-query";
import { useEffect, useReducer, useState } from "react";
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
import { sortFields } from "@/features/log/components/LogTable";
import { useSearchFieldNames } from "@/features/log/components/useLogFields";
import { LogSearchParams } from "@/features/log/LogSearchParams";
import { camelCaseToSnakeCaseString } from "@/utils/switchCase";
import { iconSize } from "@/utils/ui";

import { useLogNavigationState } from "./LogNavigationState";
import { RepoSelector } from "./RepoSelector";
import {
  FIXED_SEARCH_PARAM_NAMES,
  SearchParamFields,
  SearchParamFieldSelector,
} from "./SearchParamFields";

interface SetParamAction {
  type: "setParam";
  name: string;
  value: any;
}

interface ResetParamsAction {
  type: "resetParams";
  params?: LogSearchParams;
}

function searchParamsReducer(
  state: LogSearchParams,
  action: SetParamAction | ResetParamsAction,
): LogSearchParams {
  console.debug("searchParamsReducer", action);
  switch (action.type) {
    case "setParam":
      const update = { [action.name]: action.value };
      if (action.name === "actionCategory") {
        update["actionType"] = "";
      }
      if (action.name === "repoId") {
        update["entityRef"] = "";
      }
      return LogSearchParams.fromProperties({ ...state, ...update });
    case "resetParams":
      return LogSearchParams.fromProperties(action.params ?? {});
  }
}

function searchParamsToSearchParamNames(
  searchParams: LogSearchParams,
): Set<string> {
  const names = new Set<string>(FIXED_SEARCH_PARAM_NAMES);

  // Date
  if (searchParams.since || searchParams.until) {
    names.add("savedAt");
  }

  // Action
  if (searchParams.actionCategory) {
    names.add("actionCategory");
  }
  if (searchParams.actionType) {
    names.add("actionType");
  }

  // Actor
  if (searchParams.actorRef) {
    names.add("actorRef");
  }
  if (searchParams.actorType) {
    names.add("actorType");
  }
  searchParams.actorExtra!.forEach((_, name) => {
    names.add("actor." + name);
  });

  // Source
  searchParams.source!.forEach((_, name) => {
    names.add("source." + name);
  });

  // Resource
  if (searchParams.resourceRef) {
    names.add("resourceRef");
  }
  if (searchParams.resourceType) {
    names.add("resourceType");
  }
  searchParams.resourceExtra.forEach((_, name) => {
    names.add("resource." + name);
  });

  // Details
  searchParams.details.forEach((_, name) => {
    names.add("details." + name);
  });

  // Tag
  if (searchParams.tagRef) {
    names.add("tagRef");
  }
  if (searchParams.tagType) {
    names.add("tagType");
  }

  // Attachment
  if (searchParams.hasAttachment) {
    names.add("hasAttachment");
  }
  if (searchParams.attachmentName) {
    names.add("attachmentName");
  }
  if (searchParams.attachmentType) {
    names.add("attachmentType");
  }
  if (searchParams.attachmentMimeType) {
    names.add("attachmentMimeType");
  }

  // Entity
  if (searchParams.entityRef) {
    names.add("entity");
  }

  return names;
}

function removeSearchParam(
  searchParams: LogSearchParams,
  paramName: string,
  setSearchParam: (name: string, value: any) => void,
) {
  // Handle search params whose names are equivalent to search param names
  const equivalentSearchParams = [
    "actionCategory",
    "actionType",
    "actorRef",
    "actorType",
    "actorName",
    "resourceRef",
    "resourceType",
    "resourceName",
    "tagRef",
    "tagType",
    "tagName",
    "hasAttachment",
    "attachmentName",
    "attachmentType",
    "attachmentMimeType",
    "entityRef",
  ];
  if (equivalentSearchParams.includes(paramName)) {
    setSearchParam(paramName, "");
    return;
  }

  // Handle date
  if (paramName === "savedAt") {
    setSearchParam("since", null);
    setSearchParam("until", null);
    return;
  }

  // Handle source
  if (paramName.startsWith("source.")) {
    const fieldName = paramName.replace("source.", "");
    setSearchParam(
      "source",
      new Map([...searchParams.source].filter(([name]) => name !== fieldName)),
    );
    return;
  }

  // Handle details
  if (paramName.startsWith("details.")) {
    const fieldName = paramName.replace("details.", "");
    setSearchParam(
      "details",
      new Map([...searchParams.details].filter(([name]) => name !== fieldName)),
    );
    return;
  }

  // Handle actor custom fields
  if (paramName.startsWith("actor.")) {
    const fieldName = paramName.replace("actor.", "");
    setSearchParam(
      "actorExtra",
      new Map(
        [...searchParams.actorExtra].filter(([name]) => name !== fieldName),
      ),
    );
    return;
  }

  // Handle resource custom fields
  if (paramName.startsWith("resource.")) {
    const fieldName = paramName.replace("resource.", "");
    setSearchParam(
      "resourceExtra",
      new Map(
        [...searchParams.resourceExtra].filter(([name]) => name !== fieldName),
      ),
    );
    return;
  }

  // Handle entity
  if (paramName === "entity") {
    setSearchParam("entityRef", "");
    return;
  }

  throw new Error(`Unknown search param name: ${paramName}`);
}

function columnsToCsvColumns(columns: string[]): string[] {
  return Array.from(
    // If the user has also selected a field like "action_type", "action_category" etc..,
    // we use a Set to avoid duplicates
    new Set(
      columns
        .toSorted(sortFields)
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

function ExtraActionsCsvExport({
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

  return (
    <>
      <Menu.Label>{t("log.csv.csv")}</Menu.Label>
      <Menu.Item
        component="a"
        href={csvExportUrl}
        leftSection={<IconDownload style={iconSize(14)} />}
      >
        {t("log.csv.csvExportDefault")}
      </Menu.Item>
      <Menu.Item
        component="a"
        href={`${csvExportUrl}&columns=${columnsToCsvColumns(selectedColumns).join(",")}`}
        leftSection={<IconDownload style={iconSize(14)} />}
      >
        {t("log.csv.csvExportCurrent")}
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

function ExtraActions({
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
          <ExtraActionsCsvExport
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

export function LogNavigation({
  params,
  onChange,
  selectedColumns,
  withRepoSearchParam,
  withLogFilters,
}: {
  params: LogSearchParams;
  onChange: (params: LogSearchParams) => void;
  selectedColumns: string[];
  withRepoSearchParam: boolean;
  withLogFilters: boolean;
}) {
  const { t } = useTranslation();
  const [editedParams, dispatch] = useReducer(searchParamsReducer, params);
  const [isDirty, setIsDirty] = useState(false);
  const [searchParamNames, setSearchParamNames] = useState<Set<string>>(
    searchParamsToSearchParamNames(params),
  );
  const availableSearchParamFieldNames = useSearchFieldNames(
    editedParams.repoId,
    FIXED_SEARCH_PARAM_NAMES,
  );
  const [addedSearchParamName, setAddedSearchParamName] = useState<
    string | null
  >(null);
  const removeSearchParamField = (name: string) => {
    setSearchParamNames(
      new Set([...searchParamNames].filter((n) => n !== name)),
    );
    setAddedSearchParamName(null);
    removeSearchParam(editedParams, name, (name, value) =>
      dispatch({ type: "setParam", name, value }),
    );
    setIsDirty(true);
  };

  // Typically, an inline search param has been applied from logs table
  useEffect(() => {
    dispatch({ type: "resetParams", params });
    setIsDirty(false);
    setSearchParamNames(searchParamsToSearchParamNames(params));
    setAddedSearchParamName(null);
  }, [params]);

  // Remove search params that are not available in the selected repository
  useEffect(() => {
    if (availableSearchParamFieldNames !== null) {
      for (const paramName of searchParamNames) {
        if (!availableSearchParamFieldNames.includes(paramName)) {
          removeSearchParamField(paramName);
        }
      }
    }
  }, [availableSearchParamFieldNames]);

  const gap = rem(6);

  return (
    <Group justify="space-between" align="start" gap="md" wrap="nowrap">
      <Group gap={gap}>
        {/* Repository selector */}
        {withRepoSearchParam && (
          <RepoSelector
            repoId={editedParams.repoId}
            onChange={(repoId) => {
              dispatch({ type: "setParam", name: "repoId", value: repoId });
              setIsDirty(true);
            }}
          />
        )}

        {/* Search parameters */}
        <Group gap={gap}>
          <SearchParamFields
            names={searchParamNames}
            added={addedSearchParamName}
            searchParams={editedParams}
            onChange={(name, value) => {
              dispatch({ type: "setParam", name, value });
              setIsDirty(true);
            }}
            onRemove={removeSearchParamField}
          />
          <SearchParamFieldSelector
            repoId={editedParams.repoId}
            selected={searchParamNames}
            onSearchParamAdded={(name) => {
              setSearchParamNames(new Set([...searchParamNames, name]));
              setAddedSearchParamName(name);
            }}
            onSearchParamRemoved={removeSearchParamField}
          />
        </Group>
      </Group>

      {/* Apply & clear buttons */}
      <Group gap={gap} wrap="nowrap">
        <Button onClick={() => onChange(editedParams)} disabled={!isDirty}>
          {t("log.list.searchParams.apply")}
        </Button>
        <Button
          onClick={() => {
            {
              dispatch({
                type: "resetParams",
                params: LogSearchParams.fromProperties({
                  repoId: editedParams.repoId,
                }),
              });
              setIsDirty(true);
            }
          }}
          disabled={editedParams.isEmpty()}
          variant="default"
        >
          {t("log.list.searchParams.clear")}
        </Button>
        <ExtraActions
          searchParams={params}
          selectedColumns={selectedColumns}
          withLogFilters={withLogFilters}
        />
      </Group>
    </Group>
  );
}
