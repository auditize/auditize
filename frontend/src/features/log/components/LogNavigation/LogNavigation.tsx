import { Button, Group, rem } from "@mantine/core";
import "@tabler/icons-react";
import { useEffect, useReducer, useState } from "react";
import { useTranslation } from "react-i18next";

import { useSearchFieldNames } from "@/features/log/components/useLogFields";
import { LogSearchParams } from "@/features/log/LogSearchParams";

import { ExtraActions } from "./ExtraActions";
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
    names.add("emittedAt");
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
    "q",
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
  if (paramName === "emittedAt") {
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
            onSubmit={() => onChange(editedParams)}
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
