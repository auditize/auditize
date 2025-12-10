import { useTranslation } from "react-i18next";

import {
  getActor,
  getActorNames,
  getAllActionCategories,
  getAllActionTypes,
  getAllActorExtraFieldEnumValues,
  getAllActorTypes,
  getAllAttachmentMimeTypes,
  getAllAttachmentTypes,
  getAllDetailFieldEnumValues,
  getAllResourceExtraFieldEnumValues,
  getAllResourceTypes,
  getAllSourceFieldEnumValues,
  getAllTagTypes,
  getResource,
  getResourceNames,
  getTag,
  getTagNames,
} from "@/features/log/api";
import {
  useCustomFieldEnumValueTranslator,
  useLogTranslator,
} from "@/features/log/components/LogTranslation";
import { LogSearchParams } from "@/features/log/LogSearchParams";

import { CustomFieldSearchParamField } from "./CustomFieldSearchParamField";
import { DateInterval } from "./DateInterval";
import { EntitySearchParamField } from "./EntitySearchParamField";
import { GlobalTextSearchParamField } from "./GlobalTextSearchParamField";
import { HasAttachmentSearchParamField } from "./HasAttachmentSearchParamField";
import { SearchableSearchParamField } from "./SearchableSearchParamField";
import { SelectSearchParamField } from "./SelectSearchParamField";
import { TextInputSearchParamField } from "./TextInputSearchParamField";

export const FIXED_SEARCH_PARAM_NAMES = new Set([
  "q",
  "savedAt",
  "actorRef",
  "actionCategory",
  "actionType",
  "entity",
]);

function SearchParamField({
  name,
  searchParams,
  openedByDefault,
  onChange,
  onRemove,
  onSubmit,
}: {
  name: string;
  searchParams: LogSearchParams;
  openedByDefault: boolean;
  onChange: (name: string, value: any) => void;
  onRemove: (name: string) => void;
  onSubmit: () => void;
}) {
  const { t } = useTranslation();
  const logTranslator = useLogTranslator(searchParams.repoId);
  const customFieldEnumValueTranslator = useCustomFieldEnumValueTranslator(
    searchParams.repoId,
  );

  if (name === "q") {
    return (
      <GlobalTextSearchParamField
        searchParams={searchParams}
        onChange={onChange}
        onSubmit={onSubmit}
      />
    );
  }

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
      <CustomFieldSearchParamField
        searchParams={searchParams}
        searchParamName={name}
        enumValues={getAllActorExtraFieldEnumValues}
        enumLabel={(value) =>
          customFieldEnumValueTranslator("actor_extra_field", fieldName, value)
        }
        onChange={(_, value) =>
          onChange(
            "actorExtra",
            new Map([...searchParams.actorExtra, [fieldName, value]]),
          )
        }
        onRemove={onRemove}
        onSubmit={onSubmit}
        openedByDefault={openedByDefault}
      />
    );
  }

  if (name.startsWith("source.")) {
    const fieldName = name.replace("source.", "");
    return (
      <CustomFieldSearchParamField
        searchParams={searchParams}
        searchParamName={name}
        enumValues={getAllSourceFieldEnumValues}
        enumLabel={(value) =>
          customFieldEnumValueTranslator("source_field", fieldName, value)
        }
        onChange={(_, value) =>
          onChange(
            "source",
            new Map([...searchParams.source, [fieldName, value]]),
          )
        }
        onRemove={onRemove}
        onSubmit={onSubmit}
        openedByDefault={openedByDefault}
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
      <CustomFieldSearchParamField
        searchParams={searchParams}
        searchParamName={name}
        enumValues={getAllResourceExtraFieldEnumValues}
        enumLabel={(value) =>
          customFieldEnumValueTranslator(
            "resource_extra_field",
            fieldName,
            value,
          )
        }
        onChange={(_, value) =>
          onChange(
            "resourceExtra",
            new Map([...searchParams.resourceExtra, [fieldName, value]]),
          )
        }
        onRemove={onRemove}
        onSubmit={onSubmit}
        openedByDefault={openedByDefault}
      />
    );
  }

  if (name.startsWith("details.")) {
    const fieldName = name.replace("details.", "");
    return (
      <CustomFieldSearchParamField
        searchParams={searchParams}
        searchParamName={name}
        enumValues={getAllDetailFieldEnumValues}
        enumLabel={(value) =>
          customFieldEnumValueTranslator("detail_field", fieldName, value)
        }
        onChange={(_, value) =>
          onChange(
            "details",
            new Map([...searchParams.details, [fieldName, value]]),
          )
        }
        onRemove={onRemove}
        onSubmit={onSubmit}
        openedByDefault={openedByDefault}
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
        onSubmit={onSubmit}
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
  onSubmit,
}: {
  names: Set<string>;
  added: string | null;
  searchParams: LogSearchParams;
  onChange: (name: string, value: any) => void;
  onRemove: (name: string) => void;
  onSubmit: () => void;
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
          onSubmit={onSubmit}
        />
      ))}
    </>
  );
}
