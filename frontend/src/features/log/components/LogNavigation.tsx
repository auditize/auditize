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
  Switch,
  TextInput,
  useCombobox,
} from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import {
  IconAdjustmentsHorizontal,
  IconDeviceFloppy,
  IconDots,
  IconDownload,
  IconFilter,
  IconPlus,
} from "@tabler/icons-react";
import { useQuery } from "@tanstack/react-query";
import { useEffect, useReducer, useState } from "react";
import { useTranslation } from "react-i18next";
import { NavLink, useNavigate } from "react-router-dom";

import { CustomDateTimePicker } from "@/components";
import { CustomMultiSelect } from "@/components/CustomMultiSelect";
import { notifyError, notifySuccess } from "@/components/notifications";
import { SelectWithoutDropdown } from "@/components/SelectWithoutDropdown";
import {
  getLogFilters,
  LogFilterCreation,
  LogFilterDrawer,
  normalizeFilterColumnsForApi,
  useLogFilterMutation,
} from "@/features/log-filter";
import { useLogRepoListQuery } from "@/features/repo";
import { titlize } from "@/utils/format";
import { camelCaseToSnakeCaseString } from "@/utils/switchCase";
import { iconSize } from "@/utils/ui";

import {
  getAllAttachmentMimeTypes,
  getAllAttachmentTypes,
  getAllLogActionCategories,
  getAllLogActionTypes,
  getAllLogActorTypes,
  getAllLogNodes,
  getAllLogResourceTypes,
  getAllLogTagTypes,
} from "../api";
import { LogSearchParams } from "../LogSearchParams";
import { useLogFieldNames, useLogFields } from "./LogFieldSelector";
import { useLogNavigationState } from "./LogNavigationState";
import { sortFields } from "./LogTable";
import { useLogTranslator } from "./LogTranslation";
import { NodeSelector } from "./NodeSelector";

const FIXED_SEARCH_PARAM_NAMES = new Set([
  "savedAt",
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
  const { t } = useTranslation();
  const query = useLogRepoListQuery();

  return (
    <Select
      data={query.data?.map((repo) => ({
        label: repo.name,
        value: repo.id,
      }))}
      value={repoId || null}
      onChange={(value) => onChange(value || "")}
      placeholder={
        query.error
          ? t("common.notCurrentlyAvailable")
          : query.isPending
            ? t("common.loading")
            : undefined
      }
      disabled={query.isPending}
      clearable={false}
      display="flex"
      comboboxProps={{ withinPortal: false }}
    />
  );
}

function useLogConsolidatedDataPrefetch(repoId: string) {
  const actionCategoriesQuery = useQuery({
    queryKey: ["logConsolidatedData", "actionCategory", repoId],
    queryFn: () => getAllLogActionCategories(repoId),
    enabled: !!repoId,
  });
  const actionTypesQuery = useQuery({
    queryKey: ["logConsolidatedData", "actionType", repoId],
    queryFn: () => getAllLogActionTypes(repoId),
    enabled: !!repoId,
  });
  const actorTypesQuery = useQuery({
    queryKey: ["logConsolidatedData", "actorType", repoId],
    queryFn: () => getAllLogActorTypes(repoId),
    enabled: !!repoId,
  });
  const resourceTypesQuery = useQuery({
    queryKey: ["logConsolidatedData", "resourceType", repoId],
    queryFn: () => getAllLogResourceTypes(repoId),
    enabled: !!repoId,
  });
  const tagTypesQuery = useQuery({
    queryKey: ["logConsolidatedData", "tagType", repoId],
    queryFn: () => getAllLogTagTypes(repoId),
    enabled: !!repoId,
  });
  const attachmentTypesQuery = useQuery({
    queryKey: ["logConsolidatedData", "attachmentType", repoId],
    queryFn: () => getAllAttachmentTypes(repoId),
    enabled: !!repoId,
  });
  const attachmentMimeTypesQuery = useQuery({
    queryKey: ["logConsolidatedData", "attachmentMimeType", repoId],
    queryFn: () => getAllAttachmentMimeTypes(repoId),
    enabled: !!repoId,
  });
  const logNodesQuery = useQuery({
    queryKey: ["logConsolidatedData", "node", repoId],
    queryFn: () => getAllLogNodes(repoId),
    enabled: !!repoId,
  });
  return (
    actionCategoriesQuery.isPending ||
    actionTypesQuery.isPending ||
    actorTypesQuery.isPending ||
    resourceTypesQuery.isPending ||
    tagTypesQuery.isPending ||
    attachmentTypesQuery.isPending ||
    attachmentMimeTypesQuery.isPending ||
    logNodesQuery.isPending
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
  const { t } = useTranslation();
  const consolidatedDataQuery = useQuery({
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
    if (
      consolidatedDataQuery.data &&
      !consolidatedDataQuery.data.includes(value)
    ) {
      onChange(searchParamName, "");
    }
  }, [consolidatedDataQuery.data]);

  return (
    <SearchParamFieldPopover
      title={label}
      opened={opened}
      isSet={!!value}
      onChange={toggle}
      removable={!FIXED_SEARCH_PARAM_NAMES.has(searchParamName)}
      onRemove={() => onRemove(searchParamName)}
      loading={consolidatedDataQuery.isPending}
    >
      <SelectWithoutDropdown
        data={
          consolidatedDataQuery.data
            ? consolidatedDataQuery.data.map((item) => ({
                label: itemLabel(item),
                value: item,
              }))
            : []
        }
        value={value}
        onChange={(value) => onChange(searchParamName, value)}
        placeholder={
          consolidatedDataQuery.error
            ? t("common.notCurrentlyAvailable")
            : consolidatedDataQuery.data &&
                consolidatedDataQuery.data.length > 0
              ? label
              : t("common.notAvailable")
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
  const logNodesQuery = useQuery({
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
      loading={logNodesQuery.isPending}
    >
      <NodeSelector
        repoId={searchParams.repoId || null}
        nodeRef={searchParams.nodeRef || null}
        onChange={(value) => onChange("nodeRef", value)}
      />
    </SearchParamFieldPopover>
  );
}

function DateInterval({
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
  const [opened, { toggle }] = useDisclosure(openedByDefault);
  const [untilError, setUntilError] = useState<string | null>(null);
  const isIntervalValid = (since: Date | null, until: Date | null) =>
    !since || !until || since <= until;

  return (
    <SearchParamFieldPopover
      title={t("log.date")}
      removable={!FIXED_SEARCH_PARAM_NAMES.has("savedAt")}
      onRemove={() => onRemove("savedAt")}
      isSet={!!(searchParams.since || searchParams.until)}
      opened={opened}
      onChange={toggle}
    >
      <Stack>
        <CustomDateTimePicker
          placeholder={t("log.dateFrom")}
          value={searchParams.since}
          onChange={(since) => {
            onChange("since", since);
            setUntilError(
              isIntervalValid(since, searchParams.until)
                ? null
                : t("log.list.untilMustBeGreaterThanSince"),
            );
          }}
        />
        <CustomDateTimePicker
          placeholder={t("log.dateTo")}
          value={searchParams.until}
          onChange={(until) => {
            if (isIntervalValid(searchParams.since, until)) {
              onChange("until", until);
              setUntilError(null);
            } else {
              setUntilError(t("log.list.untilMustBeGreaterThanSince"));
            }
          }}
          initToEndOfDay
          dateTimePickerProps={{
            error: untilError ?? undefined,
            excludeDate: (until) => !isIntervalValid(searchParams.since, until),
          }}
        />
      </Stack>
    </SearchParamFieldPopover>
  );
}

function HasAttachmentSearchParamField({
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
  const [opened, { toggle }] = useDisclosure(openedByDefault);
  return (
    <SearchParamFieldPopover
      title={t("log.hasAttachment")}
      opened={opened}
      isSet={searchParams.hasAttachment !== undefined}
      onChange={toggle}
      removable={!FIXED_SEARCH_PARAM_NAMES.has("hasAttachment")}
      onRemove={() => onRemove("hasAttachment")}
    >
      <Switch
        checked={searchParams.hasAttachment ?? false}
        onChange={(event) =>
          onChange(
            "hasAttachment",
            event.currentTarget.checked ? true : undefined,
          )
        }
        label={t("log.hasAttachment")}
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

  if (name === "savedAt") {
    return (
      <DateInterval
        searchParams={searchParams}
        openedByDefault={openedByDefault}
        onChange={onChange}
        onRemove={onRemove}
      />
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

  if (name === "hasAttachment") {
    return (
      <HasAttachmentSearchParamField
        searchParams={searchParams}
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
    "search",
    FIXED_SEARCH_PARAM_NAMES,
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
    "hasAttachment",
    "attachmentName",
    "attachmentType",
    "attachmentMimeType",
    "nodeRef",
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

  // Handle node
  if (paramName === "node") {
    setSearchParam("nodeRef", "");
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
          if (column === "node") {
            return ["node_path:name"];
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

// NB: this function is a hack to avoid calling useNavigate outside react-router-dom
// in Web Component mode (where withLogFilters=false).
// Using a hook within a conditional statement should not be a problem since the
// withLogFilters has a fixed value that never changes during the lifecycle of the component.
function useRedirectToFilter(withLogFilters: boolean): (id: string) => void {
  if (withLogFilters) {
    const navigate = useNavigate();
    return (id: string) => navigate(`/logs?filterId=${id}`);
  } else {
    // will never be called
    return () => {};
  }
}

export function ExtraActions({
  searchParams: logSearchParams,
  selectedColumns,
  withLogFilters,
}: {
  searchParams: LogSearchParams;
  selectedColumns: string[];
  withLogFilters: boolean;
}) {
  const { t } = useTranslation();
  const { filterId } = useLogNavigationState();
  const redirectToFilter = useRedirectToFilter(withLogFilters);
  const [
    filterPopoverOpened,
    { open: openFilterPopover, close: closeFilterPopover },
  ] = useDisclosure(false);
  const [
    filterDrawerOpened,
    { open: openFilterDrawer, close: closeFilterDrawer },
  ] = useDisclosure(false);
  const filterListQuery = useQuery({
    queryKey: ["logFilters"],
    queryFn: () => getLogFilters().then(([filters]) => filters),
    enabled: withLogFilters,
  });
  const filterMutation = useLogFilterMutation(filterId!, {
    onSuccess: () => {
      notifySuccess(t("log.filter.updateSuccess"));
      redirectToFilter(filterId!);
    },
    onError: () => {
      notifyError(t("log.filter.updateError"));
    },
  });
  const serializedLogSearchParams = logSearchParams.serialize({
    includeRepoId: false,
    snakeCase: true,
  });
  const csvExportUrl =
    (window.auditizeBaseURL ?? "") +
    "/api/repos/" +
    logSearchParams.repoId +
    "/logs/csv?" +
    new URLSearchParams(serializedLogSearchParams).toString();

  return (
    <>
      {withLogFilters && (
        <>
          <LogFilterCreation
            repoId={logSearchParams.repoId}
            searchParams={serializedLogSearchParams}
            columns={normalizeFilterColumnsForApi(selectedColumns)}
            opened={filterPopoverOpened}
            onClose={closeFilterPopover}
          />
          <LogFilterDrawer
            opened={filterDrawerOpened}
            onClose={closeFilterDrawer}
          />
        </>
      )}
      <Menu shadow="md" withinPortal={false}>
        <Menu.Target>
          <ActionIcon size="input-sm">
            <IconDots />
          </ActionIcon>
        </Menu.Target>
        <Menu.Dropdown>
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
          {withLogFilters && (
            <>
              <Menu.Divider />
              <Menu.Label>{t("log.filter.filters")}</Menu.Label>
              {filterListQuery.data?.map((filter) => (
                <Menu.Item
                  key={filter.id}
                  component={NavLink}
                  to={`/logs?filterId=${filter.id}`}
                  leftSection={<IconFilter style={iconSize(14)} />}
                >
                  {filter.name}
                </Menu.Item>
              ))}
              {filterListQuery.data && filterListQuery.data.length > 0 && (
                <Menu.Divider />
              )}
              <Menu.Item
                component="a"
                onClick={openFilterPopover}
                leftSection={<IconDeviceFloppy style={iconSize(14)} />}
              >
                {t("log.filter.save")}
              </Menu.Item>
              {filterId && (
                <Menu.Item
                  component="a"
                  onClick={() =>
                    filterMutation.mutate({
                      searchParams: serializedLogSearchParams,
                    })
                  }
                  leftSection={<IconDeviceFloppy style={iconSize(14)} />}
                >
                  {t("log.filter.update")}
                </Menu.Item>
              )}
              <Menu.Item
                component="a"
                onClick={openFilterDrawer}
                leftSection={<IconAdjustmentsHorizontal style={iconSize(14)} />}
              >
                {t("log.filter.manage")}
              </Menu.Item>
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
  const availableSearchParamFieldNames = useLogFieldNames(
    editedParams.repoId,
    "search",
    FIXED_SEARCH_PARAM_NAMES,
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
    <Group justify="space-between" align="start" gap="md" wrap="nowrap">
      <Group gap="xs">
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
        <Group gap="xs">
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
      <Group gap="xs" wrap="nowrap">
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
