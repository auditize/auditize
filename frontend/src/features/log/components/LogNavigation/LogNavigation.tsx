import {
  ActionIcon,
  Button,
  CloseButton,
  Group,
  Menu,
  Popover,
  rem,
  Stack,
  Switch,
  TextInput,
  Tooltip,
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
import { SearchableSelectWithoutDropdown } from "@/components/SearchableSelectWithoutDropdown";
import { SelectWithoutDropdown } from "@/components/SelectWithoutDropdown";
import {
  getLogFilters,
  LogFilterCreation,
  LogFilterDrawer,
  normalizeFilterColumnsForApi,
  useLogFilterMutation,
} from "@/features/log-filter";
import {
  getActor,
  getActorNames,
  getAllActionCategories,
  getAllActionTypes,
  getAllActorTypes,
  getAllAttachmentMimeTypes,
  getAllAttachmentTypes,
  getAllLogEntities,
  getAllResourceTypes,
  getAllTagTypes,
  getResource,
  getResourceNames,
  getTag,
  getTagNames,
  NameRefPair,
} from "@/features/log/api";
import { EntitySelector } from "@/features/log/components/EntitySelector";
import { useLogNavigationState } from "@/features/log/components/LogNavigation";
import { sortFields } from "@/features/log/components/LogTable";
import { useLogTranslator } from "@/features/log/components/LogTranslation";
import {
  useSearchFieldNames,
  useSearchFields,
} from "@/features/log/components/useLogFields";
import { LogSearchParams } from "@/features/log/LogSearchParams";
import { titlize } from "@/utils/format";
import { camelCaseToSnakeCaseString } from "@/utils/switchCase";
import { iconSize } from "@/utils/ui";

import { RepoSelector } from "./RepoSelector";

const FIXED_SEARCH_PARAM_NAMES = new Set([
  "savedAt",
  "actorRef",
  "actionCategory",
  "actionType",
  "entity",
]);

function SearchParamFieldPopover({
  title,
  opened,
  isSet,
  removable = true,
  loading = false,
  focusTrap = false,
  onChange,
  onRemove,
  children,
}: {
  title: string;
  opened: boolean;
  isSet: boolean;
  removable?: boolean;
  loading?: boolean;
  focusTrap?: boolean;
  onChange: (opened: boolean) => void;
  onRemove: () => void;
  children: React.ReactNode;
}) {
  return (
    <Popover
      opened={opened}
      onChange={onChange}
      keepMounted
      trapFocus={focusTrap}
      withinPortal={false}
      shadow="md"
    >
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
      <Popover.Dropdown p="0">{children}</Popover.Dropdown>
    </Popover>
  );
}

function useLogConsolidatedDataPrefetch(repoId: string) {
  const actionCategoriesQuery = useQuery({
    queryKey: ["logConsolidatedData", "actionCategory", repoId],
    queryFn: () => getAllActionCategories(repoId),
    enabled: !!repoId,
  });
  const actionTypesQuery = useQuery({
    queryKey: ["logConsolidatedData", "actionType", repoId],
    queryFn: () => getAllActionTypes(repoId),
    enabled: !!repoId,
  });
  const actorTypesQuery = useQuery({
    queryKey: ["logConsolidatedData", "actorType", repoId],
    queryFn: () => getAllActorTypes(repoId),
    enabled: !!repoId,
  });
  const resourceTypesQuery = useQuery({
    queryKey: ["logConsolidatedData", "resourceType", repoId],
    queryFn: () => getAllResourceTypes(repoId),
    enabled: !!repoId,
  });
  const tagTypesQuery = useQuery({
    queryKey: ["logConsolidatedData", "tagType", repoId],
    queryFn: () => getAllTagTypes(repoId),
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
  const logEntitiesQuery = useQuery({
    queryKey: ["logEntities", repoId],
    queryFn: () => getAllLogEntities(repoId),
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
    logEntitiesQuery.isPending
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
      value &&
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
              ? t("common.chooseAValue")
              : t("common.noData")
        }
      />
    </SearchParamFieldPopover>
  );
}

function SearchableSearchParamField({
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
  items: (repoId: string, query: string) => Promise<NameRefPair[]>;
  itemLabel: (repoId: string, value: string) => Promise<string>;
  openedByDefault: boolean;
  onChange: (name: string, value: any) => void;
  onRemove: (name: string) => void;
}) {
  const [search, setSearch] = useState("");
  const searchQuery = useQuery({
    queryKey: ["logFieldNames", searchParamName, searchParams.repoId, search],
    queryFn: () => items(searchParams.repoId, search),
    enabled: !!searchParams.repoId && !!search,
  });
  const value = searchParams[
    searchParamName as keyof LogSearchParams
  ] as string;
  const labelQuery = useQuery({
    queryKey: [
      "logFieldNameFromRef",
      searchParamName,
      searchParams.repoId,
      value,
    ],
    queryFn: () => itemLabel(searchParams.repoId, value),
    enabled: !!searchParams.repoId && !!value,
  });
  const [opened, { toggle }] = useDisclosure(openedByDefault);

  // On repository change, reset the selected value if a corresponding
  // label cannot be found.
  useEffect(() => {
    if (value && labelQuery.data === "") {
      onChange(searchParamName, "");
    }
  }, [labelQuery.data]);

  // Build the available options from the search query if any (example: the user is performing a search)
  // or from the label query if any (example: the page is loaded with the selected value already in the URL).
  const data =
    searchQuery.isEnabled && searchQuery.data
      ? searchQuery.data.map((item) => ({
          label: item.name,
          value: item.ref,
        }))
      : labelQuery.isEnabled && labelQuery.data
        ? [
            {
              label: labelQuery.data,
              value: value,
            },
          ]
        : undefined;

  return (
    <SearchParamFieldPopover
      title={label}
      opened={opened}
      isSet={!!value}
      onChange={toggle}
      removable={!FIXED_SEARCH_PARAM_NAMES.has(searchParamName)}
      onRemove={() => onRemove(searchParamName)}
      loading={searchQuery.isEnabled && searchQuery.isPending}
    >
      <SearchableSelectWithoutDropdown
        data={data}
        value={value}
        onChange={(value) => onChange(searchParamName, value)}
        onSearchChange={setSearch}
        opened={opened}
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
  const [opened, setOpened] = useState(openedByDefault);
  return (
    <SearchParamFieldPopover
      title={label}
      opened={opened}
      isSet={!!value}
      onChange={setOpened}
      removable={!FIXED_SEARCH_PARAM_NAMES.has(name)}
      onRemove={() => onRemove(name)}
      focusTrap={true}
    >
      <TextInput
        placeholder={label}
        value={value}
        onChange={(event) => onChange(event.currentTarget.value)}
        p="sm"
        // If the label (and then the placeholder) contains the word "email" for instance,
        // a password manager will try to fill the input with an email address, which is not what we want.
        // Make a best effort to avoid this behavior
        // (see https://www.stefanjudis.com/snippets/turn-off-password-managers/).
        autoComplete="off"
        data-1p-ignore
        data-lpignore="true"
        data-form-type="other"
        data-bwignore
      />
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

function EntitySearchParamField({
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
  const logEntitiesQuery = useQuery({
    queryKey: ["logEntities", searchParams.repoId],
    queryFn: () => getAllLogEntities(searchParams.repoId),
    enabled: !!searchParams.repoId,
  });
  const [opened, { toggle }] = useDisclosure(openedByDefault);
  return (
    <SearchParamFieldPopover
      title={t("log.entity")}
      opened={opened}
      isSet={!!searchParams.entityRef}
      onChange={toggle}
      removable={!FIXED_SEARCH_PARAM_NAMES.has("entity")}
      onRemove={() => onRemove("entity")}
      loading={logEntitiesQuery.isPending}
    >
      <EntitySelector
        repoId={searchParams.repoId || null}
        entityRef={searchParams.entityRef}
        onChange={(value) => onChange("entityRef", value)}
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
      <Stack p="sm" gap="sm">
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
            excludeDate: (until) =>
              !isIntervalValid(searchParams.since, new Date(until)),
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
        p="sm"
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
        items={getAllActionCategories}
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
          getAllActionTypes(repoId, searchParams.actionCategory)
        }
        itemsQueryKeyExtra={searchParams.actionCategory}
        itemLabel={(value) => logTranslator("action_type", value)}
        openedByDefault={openedByDefault}
        onChange={onChange}
        onRemove={onRemove}
      />
    );
  }

  if (name === "actorRef") {
    return (
      <SearchableSearchParamField
        label={t("log.actor")}
        searchParams={searchParams}
        searchParamName="actorRef"
        items={getActorNames}
        itemLabel={(repoId, value) =>
          getActor(repoId, value)
            .then((actor) => actor.name)
            .catch(() => "")
        }
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
        items={getAllActorTypes}
        itemLabel={(value) => logTranslator("actor_type", value)}
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
        items={getAllResourceTypes}
        itemLabel={(value) => logTranslator("resource_type", value)}
        openedByDefault={openedByDefault}
        onChange={onChange}
        onRemove={onRemove}
      />
    );
  }

  if (name === "resourceRef") {
    return (
      <SearchableSearchParamField
        label={t("log.resource")}
        searchParams={searchParams}
        searchParamName="resourceRef"
        items={getResourceNames}
        itemLabel={(repoId, value) =>
          getResource(repoId, value)
            .then((resource) => resource.name)
            .catch(() => "")
        }
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
        items={getAllTagTypes}
        itemLabel={(value) => logTranslator("tag_type", value)}
        openedByDefault={openedByDefault}
        onChange={onChange}
        onRemove={onRemove}
      />
    );
  }

  if (name === "tagRef") {
    return (
      <SearchableSearchParamField
        label={t("log.tag")}
        searchParams={searchParams}
        searchParamName="tagRef"
        items={getTagNames}
        itemLabel={(repoId, value) =>
          getTag(repoId, value)
            .then((tag) => tag.name ?? "")
            .catch(() => "")
        }
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

  if (name === "entity") {
    return (
      <EntitySearchParamField
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
  const { fields, loading: logFieldsLoading } = useSearchFields(
    repoId,
    FIXED_SEARCH_PARAM_NAMES,
  );
  const logConsolidatedDataLoading = useLogConsolidatedDataPrefetch(repoId);
  const comboboxStore = useCombobox();
  const { t } = useTranslation();

  return (
    <CustomMultiSelect
      comboboxStore={comboboxStore}
      data={fields}
      value={Array.from(selected)}
      onOptionSubmit={onSearchParamAdded}
      onRemove={onSearchParamRemoved}
      closeOnSelect
    >
      <Tooltip
        label={t("log.list.searchParams.more")}
        disabled={comboboxStore.dropdownOpened}
        position="bottom"
        withArrow
        withinPortal={false}
      >
        <ActionIcon
          onClick={() => comboboxStore.toggleDropdown()}
          loading={logFieldsLoading || logConsolidatedDataLoading}
          loaderProps={{ type: "dots" }}
          size="input-sm"
        >
          <IconPlus />
        </ActionIcon>
      </Tooltip>
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
