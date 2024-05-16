import { Button, Group, Space, TextInput } from "@mantine/core";
import { useLocalStorage } from "@mantine/hooks";
import { useEffect, useReducer } from "react";

import {
  CustomDateTimePicker,
  PaginatedSelector,
  PopoverForm,
} from "@/components";
import { getAllMyRepos } from "@/features/repos";
import { Repo } from "@/features/repos";
import { labelize } from "@/utils/format";

import {
  buildEmptyLogsFilterParams,
  getAllLogActionCategories,
  getAllLogActionTypes,
  getAllLogActorExtraFields,
  getAllLogActorTypes,
  getAllLogResourceTypes,
  getAllLogTagTypes,
  LogsFilterParams,
} from "../api";
import { CustomFieldSelector } from "./CustomFieldSelector";
import { NodeSelector } from "./NodeSelector";

function ActionCategorySelector({
  repoId,
  category,
  onChange,
}: {
  repoId?: string;
  category?: string;
  onChange: (value: string) => void;
}) {
  return (
    <PaginatedSelector
      label="Action category"
      queryKey={["logActionCategory", repoId]}
      queryFn={() => getAllLogActionCategories(repoId!)}
      enabled={!!repoId}
      selectedItem={category}
      onChange={onChange}
      itemLabel={(item) => labelize(item)}
      itemValue={(item) => item}
    />
  );
}

function ActionTypeSelector({
  repoId,
  type,
  category,
  onChange,
}: {
  repoId?: string;
  type?: string;
  category?: string;
  onChange: (value: string) => void;
}) {
  return (
    <PaginatedSelector
      label="Action type"
      queryKey={["logActionTypes", repoId, category]}
      queryFn={() => getAllLogActionTypes(repoId!, category)}
      enabled={!!repoId}
      selectedItem={type}
      onChange={onChange}
      itemLabel={(item) => labelize(item)}
      itemValue={(item) => item}
    />
  );
}

function ActorTypeSelector({
  repoId,
  type,
  onChange,
}: {
  repoId?: string;
  type?: string;
  onChange: (value: string) => void;
}) {
  return (
    <PaginatedSelector
      label="Actor type"
      queryKey={["logActorType", repoId]}
      queryFn={() => getAllLogActorTypes(repoId!)}
      enabled={!!repoId}
      selectedItem={type}
      onChange={onChange}
      itemLabel={(item) => labelize(item)}
      itemValue={(item) => item}
    />
  );
}

function ActorExtraFieldSelector({
  repoId,
  value,
  onChange,
}: {
  repoId?: string;
  value: Map<string, string>;
  onChange: (value: Map<string, string>) => void;
}) {
  return (
    <CustomFieldSelector
      label="Custom fields"
      queryKey={["logActorExtraFields", repoId]}
      queryFn={() => getAllLogActorExtraFields(repoId!)}
      enabled={!!repoId}
      value={value}
      onChange={onChange}
      itemLabel={(item) => labelize(item)}
    />
  );
}

function ResourceTypeSelector({
  repoId,
  type,
  onChange,
}: {
  repoId?: string;
  type?: string;
  onChange: (value: string) => void;
}) {
  return (
    <PaginatedSelector
      label="Resource type"
      queryKey={["logResourceType", repoId]}
      queryFn={() => getAllLogResourceTypes(repoId!)}
      enabled={!!repoId}
      selectedItem={type}
      onChange={onChange}
      itemLabel={(item) => labelize(item)}
      itemValue={(item) => item}
    />
  );
}

function TagTypeSelector({
  repoId,
  type,
  onChange,
}: {
  repoId?: string;
  type?: string;
  onChange: (value: string) => void;
}) {
  return (
    <PaginatedSelector
      label="Tag type"
      queryKey={["logTagTypes", repoId]}
      queryFn={() => getAllLogTagTypes(repoId!)}
      enabled={!!repoId}
      selectedItem={type}
      onChange={onChange}
      itemLabel={(item) => labelize(item)}
      itemValue={(item) => item}
    />
  );
}

function RepoSelector({
  repoId,
  onChange,
}: {
  repoId?: string;
  onChange: (value: string) => void;
}) {
  const [defaultSelectedRepo, setDefaultSelectedRepo] = useLocalStorage({
    key: "default-selected-repo",
    getInitialValueInEffect: false,
  });

  // Update default-selected-repo local storage key on repoId change
  // so that the repo selector will be automatically set to the last selected repo
  // on page reload
  useEffect(() => {
    if (repoId) {
      setDefaultSelectedRepo(repoId);
    }
  }, [repoId]);

  return (
    <PaginatedSelector
      label="Repository"
      queryKey={["repos"]}
      queryFn={() => getAllMyRepos({ hasReadPermission: true })}
      selectedItem={repoId}
      clearable={false}
      onChange={onChange}
      onDataLoaded={(repos: Repo[]) => {
        // repo has not been auto-selected yet
        if (!repoId) {
          // if no default repo or default repo is not in the list, select the first one (if any)
          if (
            !defaultSelectedRepo ||
            !repos.find((repo) => repo.id === defaultSelectedRepo)
          ) {
            if (repos.length > 0) {
              onChange(repos[0].id);
            }
            // otherwise, select the default/previously selected repo (local storage)
          } else {
            onChange(defaultSelectedRepo);
          }
        }
      }}
      itemLabel={(repo) => repo.name}
      itemValue={(repo) => repo.id}
    />
  );
}

interface SetParamAction {
  type: "setParam";
  name: string;
  value: any;
}

interface ResetParamsAction {
  type: "resetParams";
  params?: LogsFilterParams;
}

function filterParamsReducer(
  state: LogsFilterParams,
  action: SetParamAction | ResetParamsAction,
): LogsFilterParams {
  console.log("filterParamsReducer", action);
  switch (action.type) {
    case "setParam":
      const update = { [action.name]: action.value };
      if (action.name === "actionCategory") {
        update["actionType"] = "";
      }
      return { ...state, ...update };
    case "resetParams":
      const newParams = buildEmptyLogsFilterParams();
      return action.params ? { ...newParams, ...action.params } : newParams;
  }
}

export function LogsFilter({
  params,
  onChange,
}: {
  params: LogsFilterParams;
  onChange: (filter: LogsFilterParams) => void;
}) {
  const [editedParams, dispatch] = useReducer(
    filterParamsReducer,
    buildEmptyLogsFilterParams(),
  );

  // Typically, an inline filter has been applied from logs table
  useEffect(() => {
    dispatch({ type: "resetParams", params });
  }, [params]);

  const changeParamHandler = (name: string) => (value: any) =>
    dispatch({ type: "setParam", name, value });
  const changeTextInputParamHandler =
    (name: string) => (e: React.ChangeEvent<HTMLInputElement>) =>
      dispatch({ type: "setParam", name, value: e.target.value });

  const hasDate = !!(editedParams.since || editedParams.until);
  const hasAction = !!(editedParams.actionCategory || editedParams.actionType);
  const hasActor = !!(
    editedParams.actorType ||
    editedParams.actorName ||
    editedParams.actorExtra!.size > 0
  );
  const hasResource = !!(
    editedParams.resourceType || editedParams.resourceName
  );
  const hasTag = !!(
    editedParams.tagType ||
    editedParams.tagName ||
    editedParams.tagRef
  );
  const hasNode = !!editedParams.nodeRef;
  const hasFilter =
    hasDate || hasAction || hasActor || hasResource || hasTag || hasNode;

  console.log("editedParams", editedParams);

  return (
    <Group p="1rem">
      {/* Repository selector */}
      <RepoSelector
        repoId={editedParams.repoId}
        onChange={(repoId) => {
          // Trigger a log search when the log repository is selected for the first time
          // so that the logs table can be populated when the page is loaded without any explicit filter
          if (!editedParams.repoId) {
            onChange({ ...editedParams, repoId });
          } else {
            dispatch({ type: "setParam", name: "repoId", value: repoId });
          }
        }}
      />

      {/* Time criteria */}
      <PopoverForm title="Date" isFilled={hasDate}>
        <CustomDateTimePicker
          placeholder="From"
          value={editedParams.since}
          onChange={changeParamHandler("since")}
        />
        <CustomDateTimePicker
          placeholder="To"
          value={editedParams.until}
          onChange={changeParamHandler("until")}
          initToEndOfDay
        />
      </PopoverForm>

      {/* Action criteria */}
      <PopoverForm title="Action" isFilled={hasAction}>
        <ActionCategorySelector
          repoId={editedParams.repoId}
          category={editedParams.actionCategory}
          onChange={changeParamHandler("actionCategory")}
        />
        <ActionTypeSelector
          repoId={editedParams.repoId}
          type={editedParams.actionType}
          category={editedParams.actionCategory}
          onChange={changeParamHandler("actionType")}
        />
      </PopoverForm>

      {/* Actor criteria */}
      <PopoverForm title="Actor" isFilled={hasActor}>
        <ActorTypeSelector
          repoId={editedParams.repoId}
          type={editedParams.actorType}
          onChange={changeParamHandler("actorType")}
        />
        <TextInput
          placeholder="Actor name"
          value={editedParams.actorName}
          onChange={changeTextInputParamHandler("actorName")}
          display={"flex"}
        />
        <ActorExtraFieldSelector
          repoId={editedParams.repoId}
          value={editedParams.actorExtra!}
          onChange={changeParamHandler("actorExtra")}
        />
      </PopoverForm>

      {/* Resource criteria */}
      <PopoverForm title="Resource" isFilled={hasResource}>
        <ResourceTypeSelector
          repoId={editedParams.repoId}
          type={editedParams.resourceType}
          onChange={changeParamHandler("resourceType")}
        />
        <TextInput
          placeholder="Resource name"
          value={editedParams.resourceName}
          onChange={changeTextInputParamHandler("resourceName")}
          display={"flex"}
        />
      </PopoverForm>

      {/* Tag criteria */}
      <PopoverForm title="Tag" isFilled={hasTag}>
        <TagTypeSelector
          repoId={editedParams.repoId}
          type={editedParams.tagType}
          onChange={changeParamHandler("tagType")}
        />
        <TextInput
          placeholder="Tag name"
          value={editedParams.tagName}
          onChange={changeTextInputParamHandler("tagName")}
          display="flex"
        />
        <TextInput
          placeholder="Tag id"
          value={editedParams.tagRef}
          onChange={changeTextInputParamHandler("tagId")}
          display="flex"
        />
      </PopoverForm>

      {/* Node criteria */}
      <PopoverForm title="Node" isFilled={!!editedParams.nodeRef}>
        <NodeSelector
          repoId={editedParams.repoId || null}
          nodeRef={editedParams.nodeRef || null}
          onChange={changeParamHandler("nodeRef")}
        />
      </PopoverForm>

      {/* Apply & clear buttons */}
      <Space w="l" />
      <Button onClick={() => onChange(editedParams)}>Apply</Button>
      <Button
        onClick={() =>
          dispatch({
            type: "resetParams",
            params: { repoId: editedParams.repoId },
          })
        }
        disabled={!hasFilter}
        variant="default"
      >
        Clear
      </Button>
    </Group>
  );
}
