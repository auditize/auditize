import {
  Button,
  CloseButton,
  Flex,
  FocusTrap,
  Group,
  Popover,
  Space,
  Stack,
  TextInput,
  useCombobox,
} from "@mantine/core";
import { useDisclosure, useLocalStorage } from "@mantine/hooks";
import { IconPlus } from "@tabler/icons-react";
import { useQuery } from "@tanstack/react-query";
import { useEffect, useReducer, useState } from "react";
import { useTranslation } from "react-i18next";

import { CustomDateTimePicker, PaginatedSelector } from "@/components";
import { CustomMultiSelect } from "@/components/CustomMultiSelect";
import { SelectWithoutDropdown } from "@/components/SelectWithoutDropdown";
import { getAllMyRepos } from "@/features/repos";
import { Repo } from "@/features/repos";
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
} from "../api";
import { useLogFields } from "./LogFieldSelector";
import { useLogTranslator } from "./LogTranslation";
import { NodeSelector } from "./NodeSelector";

const FIXED_FILTER_NAMES = new Set([
  "date",
  "actionCategory",
  "actionType",
  "node",
]);

function FilterFieldPopover({
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
    <Popover opened={opened} onChange={onChange}>
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

function FilterFieldSelect({
  label,
  searchParams,
  searchParamName,
  items,
  itemLabel,
  openedByDefault,
  onChange,
  onRemove,
}: {
  label: string;
  searchParams: LogSearchParams;
  searchParamName: string;
  items: (repoId: string) => Promise<string[]>;
  itemLabel: (value: string) => string;
  openedByDefault: boolean;
  onChange: (name: string, value: any) => void;
  onRemove: (name: string) => void;
}) {
  const { isPending, error, data } = useQuery({
    queryKey: ["logConsolidatedData", searchParamName, searchParams.repoId],
    queryFn: () => items(searchParams.repoId),
    enabled: !!searchParams.repoId,
  });
  const [opened, { toggle }] = useDisclosure(openedByDefault);
  const value = searchParams[
    searchParamName as keyof LogSearchParams
  ] as string;
  return (
    <FilterFieldPopover
      title={label}
      opened={opened}
      isSet={!!value}
      onChange={toggle}
      removable={!FIXED_FILTER_NAMES.has(searchParamName)}
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
    </FilterFieldPopover>
  );
}

function BaseFilterFieldTextInput({
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
    <FilterFieldPopover
      title={label}
      opened={opened}
      isSet={!!value}
      onChange={toggle}
      removable={!FIXED_FILTER_NAMES.has(name)}
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
    </FilterFieldPopover>
  );
}

function FilterFieldTextInput({
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
    <BaseFilterFieldTextInput
      label={label}
      name={searchParamName}
      value={value}
      openedByDefault={openedByDefault}
      onChange={(value) => onChange(searchParamName, value)}
      onRemove={onRemove}
    />
  );
}

function FilterFieldNode({
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
    <FilterFieldPopover
      title={t("log.node")}
      opened={opened}
      isSet={!!searchParams.nodeRef}
      onChange={toggle}
      removable={!FIXED_FILTER_NAMES.has("node")}
      onRemove={() => onRemove("node")}
      loading={isPending}
    >
      <NodeSelector
        repoId={searchParams.repoId || null}
        nodeRef={searchParams.nodeRef || null}
        onChange={(value) => onChange("nodeRef", value)}
      />
    </FilterFieldPopover>
  );
}

function FilterField({
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
      <FilterFieldPopover
        title={t("log.date")}
        removable={!FIXED_FILTER_NAMES.has("date")}
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
      </FilterFieldPopover>
    );
  }

  if (name === "actionCategory") {
    return (
      <FilterFieldSelect
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
      <FilterFieldSelect
        label={t("log.actionType")}
        searchParams={searchParams}
        searchParamName="actionType"
        items={(repoId) =>
          getAllLogActionTypes(repoId, searchParams.actionCategory)
        }
        itemLabel={(value) => logTranslator("action_type", value)}
        openedByDefault={openedByDefault}
        onChange={onChange}
        onRemove={onRemove}
      />
    );
  }

  if (name === "actorType") {
    return (
      <FilterFieldSelect
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
      <FilterFieldTextInput
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
      <FilterFieldTextInput
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
      <BaseFilterFieldTextInput
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
      <BaseFilterFieldTextInput
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
      <FilterFieldSelect
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
      <FilterFieldTextInput
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
      <FilterFieldTextInput
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
      <BaseFilterFieldTextInput
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
      <BaseFilterFieldTextInput
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
      <FilterFieldSelect
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
      <FilterFieldTextInput
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
      <FilterFieldTextInput
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
      <FilterFieldTextInput
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
      <FilterFieldTextInput
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
      <FilterFieldSelect
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
      <FilterFieldSelect
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
      <FilterFieldNode
        searchParams={searchParams}
        openedByDefault={openedByDefault}
        onChange={onChange}
        onRemove={onRemove}
      />
    );
  }

  return null;
}

function FilterFields({
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
        <FilterField
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

function FilterSelector({
  repoId,
  selected,
  onFilterAdded,
  onFilterRemoved,
}: {
  repoId: string;
  selected: Set<string>;
  onFilterAdded: (name: string) => void;
  onFilterRemoved: (name: string) => void;
}) {
  const { fields, loading: logFieldsLoading } = useLogFields(
    repoId,
    FIXED_FILTER_NAMES,
    false,
  );
  const logConsolidatedDataLoading = useLogConsolidatedDataPrefetch(repoId);
  const comboboxStore = useCombobox();

  return (
    <CustomMultiSelect
      comboboxStore={comboboxStore}
      data={fields}
      value={Array.from(selected)}
      onOptionSubmit={onFilterAdded}
      onRemove={onFilterRemoved}
    >
      <Button
        onClick={() => comboboxStore.toggleDropdown()}
        loading={logFieldsLoading || logConsolidatedDataLoading}
        loaderProps={{ type: "dots" }}
      >
        <IconPlus />
      </Button>
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

function filterParamsReducer(
  state: LogSearchParams,
  action: SetParamAction | ResetParamsAction,
): LogSearchParams {
  console.log("filterParamsReducer", action);
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

function searchParamsToFilterNames(searchParams: LogSearchParams): Set<string> {
  const filterNames = new Set<string>(FIXED_FILTER_NAMES);

  // Date
  if (searchParams.since || searchParams.until) {
    filterNames.add("date");
  }

  // Action
  if (searchParams.actionCategory) {
    filterNames.add("actionCategory");
  }
  if (searchParams.actionType) {
    filterNames.add("actionType");
  }

  // Actor
  if (searchParams.actorRef) {
    filterNames.add("actorRef");
  }
  if (searchParams.actorType) {
    filterNames.add("actorType");
  }
  if (searchParams.actorName) {
    filterNames.add("actorName");
  }
  searchParams.actorExtra!.forEach((_, name) => {
    filterNames.add("actor." + name);
  });

  // Source
  searchParams.source!.forEach((_, name) => {
    filterNames.add("source." + name);
  });

  // Resource
  if (searchParams.resourceRef) {
    filterNames.add("resourceRef");
  }
  if (searchParams.resourceType) {
    filterNames.add("resourceType");
  }
  if (searchParams.resourceName) {
    filterNames.add("resourceName");
  }
  searchParams.resourceExtra.forEach((_, name) => {
    filterNames.add("resource." + name);
  });

  // Details
  searchParams.details.forEach((_, name) => {
    filterNames.add("details." + name);
  });

  // Tag
  if (searchParams.tagRef) {
    filterNames.add("tagRef");
  }
  if (searchParams.tagType) {
    filterNames.add("tagType");
  }
  if (searchParams.tagName) {
    filterNames.add("tagName");
  }

  // Attachment
  if (searchParams.attachmentName) {
    filterNames.add("attachmentName");
  }
  if (searchParams.attachmentDescription) {
    filterNames.add("attachmentDescription");
  }
  if (searchParams.attachmentType) {
    filterNames.add("attachmentType");
  }
  if (searchParams.attachmentMimeType) {
    filterNames.add("attachmentMimeType");
  }

  // Node
  if (searchParams.nodeRef) {
    filterNames.add("node");
  }

  return filterNames;
}

function removeSearchParam(
  searchParams: LogSearchParams,
  filterName: string,
  setSearchParam: (name: string, value: any) => void,
) {
  // Handle search params whose names are equivalent to filter names
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
  if (equivalentSearchParams.includes(filterName)) {
    setSearchParam(filterName, "");
    return;
  }

  // Handle date
  if (filterName === "date") {
    setSearchParam("since", null);
    setSearchParam("until", null);
    return;
  }

  // Handle source
  if (filterName.startsWith("source.")) {
    const fieldName = filterName.replace("source.", "");
    setSearchParam(
      "source",
      new Map([...searchParams.source].filter(([name]) => name !== fieldName)),
    );
    return;
  }

  // Handle details
  if (filterName.startsWith("details.")) {
    const fieldName = filterName.replace("details.", "");
    setSearchParam(
      "details",
      new Map([...searchParams.details].filter(([name]) => name !== fieldName)),
    );
    return;
  }

  // Handle actor custom fields
  if (filterName.startsWith("actor.")) {
    const fieldName = filterName.replace("actor.", "");
    setSearchParam(
      "actorExtra",
      new Map(
        [...searchParams.actorExtra].filter(([name]) => name !== fieldName),
      ),
    );
    return;
  }

  // Handle resource custom fields
  if (filterName.startsWith("resource.")) {
    const fieldName = filterName.replace("resource.", "");
    setSearchParam(
      "resourceExtra",
      new Map(
        [...searchParams.resourceExtra].filter(([name]) => name !== fieldName),
      ),
    );
    return;
  }

  // Handle node
  if (filterName === "node") {
    setSearchParam("nodeRef", "");
    return;
  }

  throw new Error(`Unknown filter name: ${filterName}`);
}

export function LogFilter({
  params,
  onChange,
}: {
  params: LogSearchParams;
  onChange: (filter: LogSearchParams) => void;
}) {
  const { t } = useTranslation();
  const [editedParams, dispatch] = useReducer(filterParamsReducer, params);
  const [filterNames, setFilterNames] = useState<Set<string>>(
    searchParamsToFilterNames(params),
  );
  const [addedFilterName, setAddedFilterName] = useState<string | null>(null);

  // Typically, an inline filter has been applied from logs table
  useEffect(() => {
    dispatch({ type: "resetParams", params });
    setFilterNames(searchParamsToFilterNames(params));
  }, [params]);

  const removeFilter = (name: string) => {
    setFilterNames(new Set([...filterNames].filter((n) => n !== name)));
    removeSearchParam(editedParams, name, (name, value) =>
      dispatch({ type: "setParam", name, value }),
    );
  };

  return (
    <Flex justify="space-between" align="center">
      <Group gap="xs">
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

        {/* Filters */}
        <FilterFields
          names={filterNames}
          added={addedFilterName}
          searchParams={editedParams}
          onChange={(name, value) =>
            dispatch({ type: "setParam", name, value })
          }
          onRemove={removeFilter}
        />
        <FilterSelector
          repoId={editedParams.repoId}
          selected={filterNames}
          onFilterAdded={(name) => {
            setFilterNames(new Set([...filterNames, name]));
            setAddedFilterName(name);
          }}
          onFilterRemoved={removeFilter}
        />
      </Group>

      {/* Apply & clear buttons */}
      <Space w="l" />
      <Group>
        <Button onClick={() => onChange(editedParams)}>
          {t("log.list.filter.apply")}
        </Button>
        <Button
          onClick={() =>
            dispatch({
              type: "resetParams",
              params: {
                ...buildLogSearchParams(),
                repoId: editedParams.repoId,
              },
            })
          }
          variant="default"
        >
          {t("log.list.filter.clear")}
        </Button>
      </Group>
    </Flex>
  );
}
