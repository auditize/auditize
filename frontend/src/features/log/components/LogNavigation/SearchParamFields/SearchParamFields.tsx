import {
  Button,
  CloseButton,
  Popover,
  Stack,
  Switch,
  TextInput,
} from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { CustomDateTimePicker } from "@/components";
import { SearchableSelectWithoutDropdown } from "@/components/SearchableSelectWithoutDropdown";
import { SelectWithoutDropdown } from "@/components/SelectWithoutDropdown";
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
import { useLogTranslator } from "@/features/log/components/LogTranslation";
import { LogSearchParams } from "@/features/log/LogSearchParams";
import { titlize } from "@/utils/format";

export const FIXED_SEARCH_PARAM_NAMES = new Set([
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

export function SearchParamFields({
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
