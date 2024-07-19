import {
  ActionIcon,
  Button,
  CloseButton,
  Flex,
  FocusTrap,
  Group,
  Menu,
  Popover,
  Select,
  Space,
  Stack,
  TextInput,
  useCombobox,
} from "@mantine/core";
import { useDisclosure, useLocalStorage } from "@mantine/hooks";
import { IconDots, IconPlus } from "@tabler/icons-react";
import { useQuery } from "@tanstack/react-query";
import * as changeCase from "change-case";
import { useEffect, useReducer, useState } from "react";
import { useTranslation } from "react-i18next";
import { NavLink } from "react-router-dom";

import { CustomDateTimePicker } from "@/components";
import { CustomMultiSelect } from "@/components/CustomMultiSelect";
import { SelectWithoutDropdown } from "@/components/SelectWithoutDropdown";
import { getLogFilters, LogFilterCreation } from "@/features/logfilters";
import { titlize } from "@/utils/format";

import {
  buildLogSearchParams,
  getAllAttachmentMimeTypes,
  getAllAttachmentTypes,
  getAllLogActionCategories,
  getAllLogActionTypes,
  getAllLogActorTypes,
  getAllLogNodes,
  getAllLogResourceTypes,
  getAllLogTagTypes,
  LogSearchParams,
  logSearchParamsToURLSearchParams,
} from "../api";
import { useLogRepoQuery } from "../hooks";
import { useLogFieldNames, useLogFields } from "./LogFieldSelector";
import { sortFields } from "./LogTable";
import { useLogTranslator } from "./LogTranslation";
import { NodeSelector } from "./NodeSelector";

const FIXED_SEARCH_PARAM_NAMES = new Set([
  "date",
  "actionCategory",
  "actionType",
  "node",
]);

function SearchParamFieldPopover({
  title,
  opened,
  isSet,
  removable = true,
  loading = false,
  onChange,
  onRemove,
  children,
}: {
  title: string;
  opened: boolean;
  isSet: boolean;
  removable?: boolean;
  loading?: boolean;
  onChange: (opened: boolean) => void;
  onRemove: () => void;
  children: React.ReactNode;
}) {
  return (
    <Popover opened={opened} onChange={onChange} withinPortal={false}>
      <Popover.Target>
        <Button
          onClick={() => onChange(!opened)}
          loading={loading}
          loaderProps={{ type: "dots" }}
          rightSection={
            removable && (
              <CloseButton
                onClick={onRemove}
                component="a" // a button cannot be a child of a button
                variant="transparent"
              />
            )
          }
          variant={isSet ? "light" : "outline"}
        >
          {title}
        </Button>
      </Popover.Target>
      <Popover.Dropdown>{children}</Popover.Dropdown>
    </Popover>
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
  const repoQuery = useLogRepoQuery();

  // Update default-selected-repo local storage key on repoId change
  // so that the repo selector will be automatically set to the last selected repo
  // on page reload
  useEffect(() => {
    if (repoId) {
      setDefaultSelectedRepo(repoId);
    }
  }, [repoId]);

  useEffect(() => {
    const repos = repoQuery.data;

    // repo has not been auto-selected yet
    if (repos && !repoId) {
      // if no default repo or default repo is not in the list, select the first one (if any)
      if (
        !defaultSelectedRepo ||
        !repos.find((repo) => repo.id === defaultSelectedRepo)
      ) {
        if (repos.length > 0) {
          onChange(repos[0].id);
        }
      } else {
        // otherwise, select the default/previously selected repo (local storage)
        onChange(defaultSelectedRepo);
      }
    }
  }, [repoQuery.data]);

  return (
    <Select
      data={repoQuery.data?.map((repo) => ({
        label: repo.name,
        value: repo.id,
      }))}
      value={repoId || null}
      onChange={(value) => onChange(value || "")}
      placeholder={
        repoQuery.error
          ? "Not available"
          : repoQuery.isPending
            ? "Loading..."
            : "Repository"
      }
      disabled={repoQuery.isPending}
      clearable={false}
      display="flex"
      comboboxProps={{ withinPortal: false }}
    />
  );
}

function useLogConsolidatedDataPrefetch(repoId: string) {
  const { isPending: actionCategoryPending } = useQuery({
    queryKey: ["logConsolidatedData", "actionCategory", repoId],
    queryFn: () => getAllLogActionCategories(repoId),
    enabled: !!repoId,
  });
  const { isPending: actionTypePending } = useQuery({
    queryKey: ["logConsolidatedData", "actionType", repoId],
    queryFn: () => getAllLogActionTypes(repoId),
    enabled: !!repoId,
  });
  const { isPending: actorTypePending } = useQuery({
    queryKey: ["logConsolidatedData", "actorType", repoId],
    queryFn: () => getAllLogActorTypes(repoId),
    enabled: !!repoId,
  });
  const { isPending: resourceTypePending } = useQuery({
    queryKey: ["logConsolidatedData", "resourceType", repoId],
    queryFn: () => getAllLogResourceTypes(repoId),
    enabled: !!repoId,
  });
  const { isPending: tagTypePending } = useQuery({
    queryKey: ["logConsolidatedData", "tagType", repoId],
    queryFn: () => getAllLogTagTypes(repoId),
    enabled: !!repoId,
  });
  const { isPending: attachmentTypePending } = useQuery({
    queryKey: ["logConsolidatedData", "attachmentType", repoId],
    queryFn: () => getAllAttachmentTypes(repoId),
    enabled: !!repoId,
  });
  const { isPending: attachmentMimeTypePending } = useQuery({
    queryKey: ["logConsolidatedData", "attachmentMimeType", repoId],
    queryFn: () => getAllAttachmentMimeTypes(repoId),
    enabled: !!repoId,
  });
  const { isPending: nodePending } = useQuery({
    queryKey: ["logConsolidatedData", "node", repoId],
    queryFn: () => getAllLogNodes(repoId),
    enabled: !!repoId,
  });
  return (
    actionCategoryPending ||
    actionTypePending ||
    actorTypePending ||
    resourceTypePending ||
    tagTypePending ||
    attachmentTypePending ||
    attachmentMimeTypePending ||
    nodePending
  );
}

function SelectSearchParamField({
  label,
  searchParams,
  searchParamName,
  items,
  itemsQueryKeyExtra,
  itemLabel,
  openedByDefault,
  onChange,
  onRemove,
}: {
  label: string;
  searchParams: LogSearchParams;
  searchParamName: string;
  items: (repoId: string) => Promise<string[]>;
  itemsQueryKeyExtra?: string;
  itemLabel: (value: string) => string;
  openedByDefault: boolean;
  onChange: (name: string, value: any) => void;
  onRemove: (name: string) => void;
}) {
  const { isPending, error, data } = useQuery({
    queryKey: [
      "logConsolidatedData",
      searchParamName,
      searchParams.repoId,
      itemsQueryKeyExtra,
    ],
    queryFn: () => items(searchParams.repoId),
    enabled: !!searchParams.repoId,
  });
  const [opened, { toggle }] = useDisclosure(openedByDefault);
  const value = searchParams[
    searchParamName as keyof LogSearchParams
  ] as string;

  useEffect(() => {
    // on repository change, reset the selected value if it's not in the new data
    if (data && !data.includes(value)) {
      onChange(searchParamName, "");
    }
  }, [data]);

  return (
    <SearchParamFieldPopover
      title={label}
      opened={opened}
      isSet={!!value}
      onChange={toggle}
      removable={!FIXED_SEARCH_PARAM_NAMES.has(searchParamName)}
      onRemove={() => onRemove(searchParamName)}
      loading={isPending}
    >
      <SelectWithoutDropdown
        data={
          data
            ? data.map((item) => ({
                label: itemLabel(item),
                value: item,
              }))
            : []
        }
        value={value}
        onChange={(value) => onChange(searchParamName, value)}
        placeholder={
          error
            ? "Not currently available"
            : data && data.length > 0
              ? label
              : "No data available"
        }
      />
    </SearchParamFieldPopover>
  );
}

function BaseTextInputSearchParamField({
  label,
  name,
  value,
  openedByDefault,
  onChange,
  onRemove,
}: {
  label: string;
  name: string;
  value: string;
  openedByDefault: boolean;
  onChange: (value: any) => void;
  onRemove: (name: string) => void;
}) {
  const [opened, { toggle }] = useDisclosure(openedByDefault);
  return (
    <SearchParamFieldPopover
      title={label}
      opened={opened}
      isSet={!!value}
      onChange={toggle}
      removable={!FIXED_SEARCH_PARAM_NAMES.has(name)}
      onRemove={() => onRemove(name)}
    >
      <FocusTrap active>
        <TextInput
          placeholder={label}
          value={value}
          onChange={(event) => onChange(event.currentTarget.value)}
          data-autofocus
        />
      </FocusTrap>
    </SearchParamFieldPopover>
  );
}

function TextInputSearchParamField({
  label,
  searchParams,
  searchParamName,
  openedByDefault,
  onChange,
  onRemove,
}: {
  label: string;
  searchParams: LogSearchParams;
  searchParamName: string;
  openedByDefault: boolean;
  onChange: (name: string, value: any) => void;
  onRemove: (name: string) => void;
}) {
  const value = searchParams[
    searchParamName as keyof LogSearchParams
  ] as string;
  return (
    <BaseTextInputSearchParamField
      label={label}
      name={searchParamName}
      value={value}
      openedByDefault={openedByDefault}
      onChange={(value) => onChange(searchParamName, value)}
      onRemove={onRemove}
    />
  );
}

function NodeSearchParamField({
  searchParams,
  openedByDefault,
  onChange,
  onRemove,
}: {
  searchParams: LogSearchParams;
  openedByDefault: boolean;
  onChange: (name: string, value: any) => void;
  onRemove: (name: string) => void;
}) {
  const { t } = useTranslation();
  const { isPending } = useQuery({
    queryKey: ["logConsolidatedData", "node", searchParams.repoId],
    queryFn: () => getAllLogNodes(searchParams.repoId),
    enabled: !!searchParams.repoId,
  });
  const [opened, { toggle }] = useDisclosure(openedByDefault);
  return (
    <SearchParamFieldPopover
      title={t("log.node")}
      opened={opened}
      isSet={!!searchParams.nodeRef}
      onChange={toggle}
      removable={!FIXED_SEARCH_PARAM_NAMES.has("node")}
      onRemove={() => onRemove("node")}
      loading={isPending}
    >
      <NodeSelector
        repoId={searchParams.repoId || null}
        nodeRef={searchParams.nodeRef || null}
        onChange={(value) => onChange("nodeRef", value)}
      />
    </SearchParamFieldPopover>
  );
}

function SearchParamField({
  name,
  searchParams,
  openedByDefault,
  onChange,
  onRemove,
}: {
  name: string;
  searchParams: LogSearchParams;
  openedByDefault: boolean;
  onChange: (name: string, value: any) => void;
  onRemove: (name: string) => void;
}) {
  const { t } = useTranslation();
  const logTranslator = useLogTranslator(searchParams.repoId);
  if (name === "date") {
    // FIXME: don't use useDisclosure here
    const [opened, { toggle }] = useDisclosure(openedByDefault);
    return (
      <SearchParamFieldPopover
        title={t("log.date")}
        removable={!FIXED_SEARCH_PARAM_NAMES.has("date")}
        onRemove={() => onRemove("date")}
        isSet={!!(searchParams.since || searchParams.until)}
        opened={opened}
        onChange={toggle}
      >
        <Stack>
          <CustomDateTimePicker
            placeholder={t("log.dateFrom")}
            value={searchParams.since}
            onChange={(value) => onChange("since", value)}
          />
          <CustomDateTimePicker
            placeholder={t("log.dateTo")}
            value={searchParams.until}
            onChange={(value) => onChange("until", value)}
            initToEndOfDay
          />
        </Stack>
      </SearchParamFieldPopover>
    );
  }

  if (name === "actionCategory") {
    return (
      <SelectSearchParamField
        label={t("log.actionCategory")}
        searchParams={searchParams}
        searchParamName="actionCategory"
        items={getAllLogActionCategories}
        itemLabel={(value) => logTranslator("action_category", value)}
        openedByDefault={openedByDefault}
        onChange={onChange}
        onRemove={onRemove}
      />
    );
  }

  if (name === "actionType") {
    return (
      <SelectSearchParamField
        label={t("log.actionType")}
        searchParams={searchParams}
        searchParamName="actionType"
        items={(repoId) =>
          getAllLogActionTypes(repoId, searchParams.actionCategory)
        }
        itemsQueryKeyExtra={searchParams.actionCategory}
        itemLabel={(value) => logTranslator("action_type", value)}
        openedByDefault={openedByDefault}
        onChange={onChange}
        onRemove={onRemove}
      />
    );
  }

  if (name === "actorType") {
    return (
      <SelectSearchParamField
        label={t("log.actorType")}
        searchParams={searchParams}
        searchParamName="actorType"
        items={getAllLogActorTypes}
        itemLabel={(value) => logTranslator("actor_type", value)}
        openedByDefault={openedByDefault}
        onChange={onChange}
        onRemove={onRemove}
      />
    );
  }

  if (name === "actorName") {
    return (
      <TextInputSearchParamField
        label={t("log.actorName")}
        searchParams={searchParams}
        searchParamName="actorName"
        openedByDefault={openedByDefault}
        onChange={onChange}
        onRemove={onRemove}
      />
    );
  }

  if (name === "actorRef") {
    return (
      <TextInputSearchParamField
        label={t("log.actorRef")}
        searchParams={searchParams}
        searchParamName="actorRef"
        openedByDefault={openedByDefault}
        onChange={onChange}
        onRemove={onRemove}
      />
    );
  }

  if (name.startsWith("actor.")) {
    const fieldName = name.replace("actor.", "");
    return (
      <BaseTextInputSearchParamField
        label={t("log.actor") + ": " + titlize(fieldName)}
        name={name}
        value={searchParams.actorExtra.get(fieldName) ?? ""}
        openedByDefault={openedByDefault}
        onChange={(value) =>
          onChange(
            "actorExtra",
            new Map([...searchParams.actorExtra, [fieldName, value]]),
          )
        }
        onRemove={onRemove}
      />
    );
  }

  if (name.startsWith("source.")) {
    const fieldName = name.replace("source.", "");
    return (
      <BaseTextInputSearchParamField
        label={titlize(fieldName)}
        name={name}
        value={searchParams.source.get(fieldName) ?? ""}
        openedByDefault={openedByDefault}
        onChange={(value) =>
          onChange(
            "source",
            new Map([...searchParams.source, [fieldName, value]]),
          )
        }
        onRemove={onRemove}
      />
    );
  }

  if (name === "resourceType") {
    return (
      <SelectSearchParamField
        label={t("log.resourceType")}
        searchParams={searchParams}
        searchParamName="resourceType"
        items={getAllLogResourceTypes}
        itemLabel={(value) => logTranslator("resource_type", value)}
        openedByDefault={openedByDefault}
        onChange={onChange}
        onRemove={onRemove}
      />
    );
  }

  if (name === "resourceName") {
    return (
      <TextInputSearchParamField
        label={t("log.resourceName")}
        searchParams={searchParams}
        searchParamName="resourceName"
        openedByDefault={openedByDefault}
        onChange={onChange}
        onRemove={onRemove}
      />
    );
  }

  if (name === "resourceRef") {
    return (
      <TextInputSearchParamField
        label={t("log.resourceRef")}
        searchParams={searchParams}
        searchParamName="resourceRef"
        openedByDefault={openedByDefault}
        onChange={onChange}
        onRemove={onRemove}
      />
    );
  }

  if (name.startsWith("resource.")) {
    const fieldName = name.replace("resource.", "");
    return (
      <BaseTextInputSearchParamField
        label={t("log.resource") + ": " + titlize(fieldName)}
        name={name}
        value={searchParams.resourceExtra.get(fieldName) ?? ""}
        openedByDefault={openedByDefault}
        onChange={(value) =>
          onChange(
            "resourceExtra",
            new Map([...searchParams.resourceExtra, [fieldName, value]]),
          )
        }
        onRemove={onRemove}
      />
    );
  }

  if (name.startsWith("details.")) {
    const fieldName = name.replace("details.", "");
    return (
      <BaseTextInputSearchParamField
        label={titlize(fieldName)}
        name={name}
        value={searchParams.details!.get(fieldName) ?? ""}
        openedByDefault={openedByDefault}
        onChange={(value) =>
          onChange(
            "details",
            new Map([...searchParams.details!, [fieldName, value]]),
          )
        }
        onRemove={onRemove}
      />
    );
  }

  if (name === "tagType") {
    return (
      <SelectSearchParamField
        label={t("log.tagType")}
        searchParams={searchParams}
        searchParamName="tagType"
        items={getAllLogTagTypes}
        itemLabel={(value) => logTranslator("tag_type", value)}
        openedByDefault={openedByDefault}
        onChange={onChange}
        onRemove={onRemove}
      />
    );
  }

  if (name === "tagName") {
    return (
      <TextInputSearchParamField
        label={t("log.tagName")}
        searchParams={searchParams}
        searchParamName="tagName"
        openedByDefault={openedByDefault}
        onChange={onChange}
        onRemove={onRemove}
      />
    );
  }

  if (name === "tagRef") {
    return (
      <TextInputSearchParamField
        label={t("log.tagRef")}
        searchParams={searchParams}
        searchParamName="tagRef"
        openedByDefault={openedByDefault}
        onChange={onChange}
        onRemove={onRemove}
      />
    );
  }

  if (name === "attachmentName") {
    return (
      <TextInputSearchParamField
        label={t("log.attachmentName")}
        searchParams={searchParams}
        searchParamName="attachmentName"
        openedByDefault={openedByDefault}
        onChange={onChange}
        onRemove={onRemove}
      />
    );
  }

  if (name === "attachmentDescription") {
    return (
      <TextInputSearchParamField
        label={t("log.attachmentDescription")}
        searchParams={searchParams}
        searchParamName="attachmentDescription"
        openedByDefault={openedByDefault}
        onChange={onChange}
        onRemove={onRemove}
      />
    );
  }

  if (name === "attachmentType") {
    return (
      <SelectSearchParamField
        label={t("log.attachmentType")}
        searchParams={searchParams}
        searchParamName="attachmentType"
        items={(repoId) => getAllAttachmentTypes(repoId)}
        itemLabel={(value) => logTranslator("attachment_type", value)}
        openedByDefault={openedByDefault}
        onChange={onChange}
        onRemove={onRemove}
      />
    );
  }

  if (name === "attachmentMimeType") {
    return (
      <SelectSearchParamField
        label={t("log.attachmentMimeType")}
        searchParams={searchParams}
        searchParamName="attachmentMimeType"
        items={(repoId) => getAllAttachmentMimeTypes(repoId)}
        itemLabel={(value) => value}
        openedByDefault={openedByDefault}
        onChange={onChange}
        onRemove={onRemove}
      />
    );
  }

  if (name === "node") {
    return (
      <NodeSearchParamField
        searchParams={searchParams}
        openedByDefault={openedByDefault}
        onChange={onChange}
        onRemove={onRemove}
      />
    );
  }

  return null;
}

function SearchParamFields({
  names,
  added,
  searchParams,
  onChange,
  onRemove,
}: {
  names: Set<string>;
  added: string | null;
  searchParams: LogSearchParams;
  onChange: (name: string, value: any) => void;
  onRemove: (name: string) => void;
}) {
  return (
    <>
      {Array.from(names).map((name) => (
        <SearchParamField
          key={name}
          name={name}
          searchParams={searchParams}
          openedByDefault={name === added}
          onChange={onChange}
          onRemove={onRemove}
        />
      ))}
    </>
  );
}

function SearchParamFieldSelector({
  repoId,
  selected,
  onSearchParamAdded,
  onSearchParamRemoved,
}: {
  repoId: string;
  selected: Set<string>;
  onSearchParamAdded: (name: string) => void;
  onSearchParamRemoved: (name: string) => void;
}) {
  const { fields, loading: logFieldsLoading } = useLogFields(
    repoId,
    FIXED_SEARCH_PARAM_NAMES,
    false,
  );
  const logConsolidatedDataLoading = useLogConsolidatedDataPrefetch(repoId);
  const comboboxStore = useCombobox();

  return (
    <CustomMultiSelect
      comboboxStore={comboboxStore}
      data={fields}
      value={Array.from(selected)}
      onOptionSubmit={onSearchParamAdded}
      onRemove={onSearchParamRemoved}
    >
      <ActionIcon
        onClick={() => comboboxStore.toggleDropdown()}
        loading={logFieldsLoading || logConsolidatedDataLoading}
        loaderProps={{ type: "dots" }}
        size="input-sm"
      >
        <IconPlus />
      </ActionIcon>
    </CustomMultiSelect>
  );
}

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
  console.log("searchParamsReducer", action);
  switch (action.type) {
    case "setParam":
      const update = { [action.name]: action.value };
      if (action.name === "actionCategory") {
        update["actionType"] = "";
      }
      return { ...state, ...update };
    case "resetParams":
      const newParams = buildLogSearchParams();
      return action.params ? { ...newParams, ...action.params } : newParams;
  }
}

function searchParamsToSearchParamNames(
  searchParams: LogSearchParams,
): Set<string> {
  const names = new Set<string>(FIXED_SEARCH_PARAM_NAMES);

  // Date
  if (searchParams.since || searchParams.until) {
    names.add("date");
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
  if (searchParams.actorName) {
    names.add("actorName");
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
  if (searchParams.resourceName) {
    names.add("resourceName");
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
  if (searchParams.tagName) {
    names.add("tagName");
  }

  // Attachment
  if (searchParams.attachmentName) {
    names.add("attachmentName");
  }
  if (searchParams.attachmentDescription) {
    names.add("attachmentDescription");
  }
  if (searchParams.attachmentType) {
    names.add("attachmentType");
  }
  if (searchParams.attachmentMimeType) {
    names.add("attachmentMimeType");
  }

  // Node
  if (searchParams.nodeRef) {
    names.add("node");
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
    "attachmentName",
    "attachmentDescription",
    "attachmentType",
    "attachmentMimeType",
    "nodeRef",
  ];
  if (equivalentSearchParams.includes(paramName)) {
    setSearchParam(paramName, "");
    return;
  }

  // Handle date
  if (paramName === "date") {
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

  // Handle node
  if (paramName === "node") {
    setSearchParam("nodeRef", "");
    return;
  }

  throw new Error(`Unknown search param name: ${paramName}`);
}

function columnsToCsvFields(columns: string[]): string[] {
  return columns
    .toSorted(sortFields)
    .map((column) => {
      if (column.includes(".")) {
        // make a special case for custom fields (that contains ".") because
        // changeCase.snakeCase transforms "." to "_"
        // it assumes that the custom field group is all lowercase (which is currently true:
        // actor, source, resource, details)
        return [column];
      }
      if (column === "date") {
        return ["saved_at"];
      }
      if (column === "actor") {
        return ["actor_name"];
      }
      if (column === "action") {
        return ["action_type", "action_category"];
      }
      if (column === "resource") {
        return ["resource_type", "resource_name"];
      }
      if (column === "node") {
        return ["node_path:name"];
      }
      if (column === "tag") {
        return ["tag_type"];
      }
      if (column === "attachment") {
        return ["attachment_name"];
      }
      return [changeCase.snakeCase(column)];
    })
    .flat();
}

function columnsToFilterColumns(columns: string[]): string[] {
  return columns.toSorted(sortFields).map((column) => {
    if (column.includes(".")) {
      // make a special case for custom fields (that contains ".") because
      // changeCase.snakeCase transforms "." to "_"
      // it assumes that the custom field group is all lowercase (which is currently true:
      // actor, source, resource, details)
      return column;
    }
    if (column === "date") {
      return "saved_at";
    }
    return changeCase.snakeCase(column);
  });
}

export function ExtraLogActions({
  searchParams,
  selectedColumns,
}: {
  searchParams: LogSearchParams;
  selectedColumns: string[];
}) {
  const { t } = useTranslation();
  const [
    filterPopoverOpened,
    { open: openFilterPopover, close: closeFilterPopover },
  ] = useDisclosure(false);
  const filterQuery = useQuery({
    queryKey: ["logFilters"],
    queryFn: () => getLogFilters().then(([filters]) => filters),
  });
  const normalizedSearchParams = logSearchParamsToURLSearchParams(
    searchParams,
    { includeRepoId: false, snakecase: true },
  );
  const csvExportUrl = `/api/repos/${searchParams.repoId}/logs/csv?${normalizedSearchParams.toString()}`;

  return (
    <>
      <LogFilterCreation
        repoId={searchParams.repoId}
        searchParams={Object.fromEntries(normalizedSearchParams)}
        columns={columnsToFilterColumns(selectedColumns)}
        opened={filterPopoverOpened}
        onClose={closeFilterPopover}
      />
      <Menu>
        <Menu.Target>
          <ActionIcon size="input-sm">
            <IconDots />
          </ActionIcon>
        </Menu.Target>
        <Menu.Dropdown>
          <Menu.Label>{t("log.csv.csv")}</Menu.Label>
          <Menu.Item component="a" href={csvExportUrl}>
            {t("log.csv.csvExportDefault")}
          </Menu.Item>
          <Menu.Item
            component="a"
            href={`${csvExportUrl}&fields=${columnsToCsvFields(selectedColumns).join(",")}`}
          >
            {t("log.csv.csvExportCurrent")}
          </Menu.Item>
          <Menu.Label>{t("log.filter.filter")}</Menu.Label>
          {filterQuery.data?.map((filter) => (
            <Menu.Item
              key={filter.id}
              component={NavLink}
              to={`/logs?filterId=${filter.id}`}
            >
              {filter.name}
            </Menu.Item>
          ))}
          <Menu.Item component="a" onClick={openFilterPopover}>
            {t("log.filter.save")}
          </Menu.Item>
        </Menu.Dropdown>
      </Menu>
    </>
  );
}

export function LogNavigation({
  params,
  onChange,
  selectedColumns,
  withRepoSearchParam = true,
}: {
  params: LogSearchParams;
  onChange: (params: LogSearchParams) => void;
  selectedColumns: string[];
  withRepoSearchParam?: boolean;
}) {
  const { t } = useTranslation();
  const [editedParams, dispatch] = useReducer(searchParamsReducer, params);
  const [isDirty, setIsDirty] = useState(false);
  const [searchParamNames, setSearchParamNames] = useState<Set<string>>(
    searchParamsToSearchParamNames(params),
  );
  const availableSearchParamFieldNames = useLogFieldNames(
    editedParams.repoId,
    FIXED_SEARCH_PARAM_NAMES,
    false,
  );
  const [addedSearchParamName, setAddedSearchParamName] = useState<
    string | null
  >(null);
  const removeSearchParamField = (name: string) => {
    setSearchParamNames(
      new Set([...searchParamNames].filter((n) => n !== name)),
    );
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

  return (
    <Flex justify="space-between" align="center">
      <Group gap="xs">
        {/* Repository selector */}
        {withRepoSearchParam && (
          <RepoSelector
            repoId={editedParams.repoId}
            onChange={(repoId) => {
              // Trigger a log search when the log repository is selected for the first time
              // so that the logs table can be populated when the page is loaded without any
              // explicit search parameter
              if (!editedParams.repoId) {
                onChange({ ...editedParams, repoId });
              } else {
                dispatch({ type: "setParam", name: "repoId", value: repoId });
                setIsDirty(true);
              }
            }}
          />
        )}

        {/* Search parameters */}
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

      {/* Apply & clear buttons */}
      <Space w="l" />
      <Group>
        <Button onClick={() => onChange(editedParams)} disabled={!isDirty}>
          {t("log.list.searchParams.apply")}
        </Button>
        <Button
          onClick={() => {
            {
              dispatch({
                type: "resetParams",
                params: {
                  ...buildLogSearchParams(),
                  repoId: editedParams.repoId,
                },
              });
              setIsDirty(true);
            }
          }}
          disabled={[
            editedParams.actionCategory,
            editedParams.actionType,
            editedParams.actorType,
            editedParams.actorName,
            editedParams.actorRef,
            editedParams.actorExtra.size > 0,
            editedParams.source.size > 0,
            editedParams.resourceType,
            editedParams.resourceName,
            editedParams.resourceRef,
            editedParams.resourceExtra.size > 0,
            editedParams.details.size > 0,
            editedParams.tagRef,
            editedParams.tagType,
            editedParams.tagName,
            editedParams.attachmentName,
            editedParams.attachmentDescription,
            editedParams.attachmentType,
            editedParams.attachmentMimeType,
            editedParams.nodeRef,
            editedParams.since,
            editedParams.until,
          ].every((value) => !value)}
          variant="default"
        >
          {t("log.list.searchParams.clear")}
        </Button>
        <ExtraLogActions
          searchParams={params}
          selectedColumns={selectedColumns}
        />
      </Group>
    </Flex>
  );
}
