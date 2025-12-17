import { Text } from "@mantine/core";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import {
  getAllActorExtraFields,
  getAllDetailFields,
  getAllResourceExtraFields,
  getAllSourceFields,
} from "../api";
import { AvailableCustomField, CustomFieldType } from "../api";
import { useLogTranslationQuery, useLogTranslator } from "./LogTranslation";

function useCustomFields(repoId: string) {
  const actorExtraFieldListQuery = useQuery({
    queryKey: ["logActorExtraFields", repoId],
    queryFn: () => getAllActorExtraFields(repoId),
    enabled: !!repoId,
  });
  const resourceExtraFieldListQuery = useQuery({
    queryKey: ["logResourceExtraFields", repoId],
    queryFn: () => getAllResourceExtraFields(repoId),
    enabled: !!repoId,
  });
  const detailFieldListQuery = useQuery({
    queryKey: ["logDetailFields", repoId],
    queryFn: () => getAllDetailFields(repoId),
    enabled: !!repoId,
  });
  const sourceFieldListQuery = useQuery({
    queryKey: ["logSourceFields", repoId],
    queryFn: () => getAllSourceFields(repoId),
    enabled: !!repoId,
  });
  return {
    actorExtraFields: actorExtraFieldListQuery.data ?? [],
    resourceExtraFields: resourceExtraFieldListQuery.data ?? [],
    detailFields: detailFieldListQuery.data ?? [],
    sourceFields: sourceFieldListQuery.data ?? [],
    loading:
      actorExtraFieldListQuery.isPending ||
      resourceExtraFieldListQuery.isPending ||
      detailFieldListQuery.isPending ||
      sourceFieldListQuery.isPending,
  };
}

export function useCustomFieldTypes(repoId: string) {
  const { actorExtraFields, resourceExtraFields, detailFields, sourceFields } =
    useCustomFields(repoId);
  return {
    ...Object.fromEntries(
      actorExtraFields.map((field) => [`actor.${field.name}`, field.type]),
    ),
    ...Object.fromEntries(
      sourceFields.map((field) => [`source.${field.name}`, field.type]),
    ),
    ...Object.fromEntries(
      resourceExtraFields.map((field) => [
        `resource.${field.name}`,
        field.type,
      ]),
    ),
    ...Object.fromEntries(
      detailFields.map((field) => [`details.${field.name}`, field.type]),
    ),
  };
}

export function useSearchFields(repoId: string, disabledFields?: Set<string>) {
  const { t } = useTranslation();
  const logTranslator = useLogTranslator(repoId);
  const logTranslationQuery = useLogTranslationQuery(repoId);
  const {
    actorExtraFields,
    resourceExtraFields,
    detailFields,
    sourceFields,
    loading: customFieldsLoading,
  } = useCustomFields(repoId);

  const item = (value: string, label?: string) => ({
    value,
    label: label ?? t(`log.${value}`),
    disabled: disabledFields && disabledFields.has(value),
  });
  const customFieldItems = (
    fields: AvailableCustomField[],
    prefix: string,
    translationKey: string,
  ) => {
    return (
      fields
        // Datetime values should be searchable using a range picker, which is not supported yet
        // so we hide them for now
        .filter((field) => field.type !== CustomFieldType.DateTime)
        .map((field) =>
          item(
            `${prefix}.${field.name}`,
            logTranslator(translationKey, field.name),
          ),
        )
    );
  };
  return {
    fields: [
      { group: "Date", items: [item("emittedAt", t("log.date"))] },
      { group: "Search", items: [item("q", t("common.search"))] },
      {
        group: t("log.action"),
        items: [
          item("actionCategory", t("common.category")),
          item("actionType", t("common.type")),
        ],
      },
      {
        group: t("log.actor"),
        items: [
          item("actorType", t("common.type")),
          item("actorRef", t("log.actor")),
          ...customFieldItems(
            actorExtraFields,
            "actor",
            "actor_extra_field_name",
          ),
        ],
      },
      {
        group: t("log.source"),
        items: customFieldItems(sourceFields, "source", "source_field_name"),
      },
      {
        group: t("log.resource"),
        items: [
          item("resourceRef", t("log.resource")),
          item("resourceType", t("common.type")),
          ...customFieldItems(
            resourceExtraFields,
            "resource",
            "resource_extra_field_name",
          ),
        ],
      },
      {
        group: t("log.details"),
        items: customFieldItems(detailFields, "details", "detail_field_name"),
      },
      {
        group: t("log.tag"),
        items: [
          item("tagRef", t("log.tag")),
          item("tagType", t("common.type")),
        ],
      },
      {
        group: t("log.attachment"),
        items: [
          item("hasAttachment"),
          item("attachmentName", t("common.name")),
          item("attachmentType", t("common.type")),
          item("attachmentMimeType", t("common.mimeType")),
        ],
      },
      {
        group: t("log.entity"),
        items: [item("entity")],
      },
    ],
    loading: customFieldsLoading || logTranslationQuery.isPending,
  };
}

export function useColumnFields(repoId: string) {
  const { t } = useTranslation();
  const logTranslator = useLogTranslator(repoId);
  const logTranslationQuery = useLogTranslationQuery(repoId);
  const {
    actorExtraFields,
    resourceExtraFields,
    detailFields,
    sourceFields,
    loading: customFieldsLoading,
  } = useCustomFields(repoId);

  const item = (
    value: string,
    label: string,
    renderedLabel?: React.ReactNode,
  ) => ({
    value,
    label,
    renderedLabel,
  });

  const strongItem = (value: string, label: string) =>
    item(
      value,
      label,
      <Text size="sm" fw={650}>
        {label}
      </Text>,
    );

  const customFieldItems = (
    fields: AvailableCustomField[],
    prefix: string,
    translationKey: string,
  ) => {
    return (
      fields
        // JSON fields won't probably be readable in a table, so we ignore them
        .filter((field) => field.type !== CustomFieldType.Json)
        .map((field) =>
          item(
            `${prefix}.${field.name}`,
            logTranslator(translationKey, field.name),
          ),
        )
    );
  };

  return {
    fields: [
      { group: t("log.date"), items: [item("emittedAt", t("log.date"))] },
      {
        group: "Action",
        items: [
          strongItem("action", t("log.action")),
          item("actionCategory", t("common.category")),
          item("actionType", t("common.type")),
        ],
      },
      {
        group: t("log.actor"),
        items: [
          strongItem("actor", t("log.actor")),
          item("actorType", t("common.type")),
          item("actorName", t("common.name")),
          item("actorRef", t("common.ref")),
          ...customFieldItems(
            actorExtraFields,
            "actor",
            "actor_extra_field_name",
          ),
        ],
      },
      {
        group: t("log.source"),
        items: customFieldItems(sourceFields, "source", "source_field_name"),
      },
      {
        group: t("log.resource"),
        items: [
          strongItem("resource", t("log.resource")),
          item("resourceType", t("common.type")),
          item("resourceName", t("common.name")),
          item("resourceRef", t("common.ref")),
          ...customFieldItems(
            resourceExtraFields,
            "resource",
            "resource_extra_field_name",
          ),
        ],
      },
      {
        group: t("log.details"),
        items: customFieldItems(detailFields, "details", "detail_field_name"),
      },
      {
        group: t("log.tag"),
        items: [
          strongItem("tag", t("log.tag")),
          item("tagType", t("common.type")),
          item("tagName", t("common.name")),
          item("tagRef", t("common.ref")),
        ],
      },
      {
        group: "Attachment",
        items: [
          strongItem("attachment", t("log.attachment")),
          item("hasAttachment", t("log.hasAttachment")),
          item("attachmentName", t("common.name")),
          item("attachmentType", t("common.type")),
          item("attachmentMimeType", t("common.mimeType")),
        ],
      },
      {
        group: t("log.entity"),
        items: [item("entity", t("log.entity"))],
      },
    ],
    loading: customFieldsLoading || logTranslationQuery.isPending,
  };
}

export function useSearchFieldNames(
  repoId: string,
  disabledFields?: Set<string>,
) {
  const { fields, loading } = useSearchFields(repoId, disabledFields);
  return loading
    ? null
    : fields.map((group) => group.items.map((item) => item.value)).flat();
}
