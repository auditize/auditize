import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import {
  getAllActorCustomFields,
  getAllDetailFields,
  getAllResourceCustomFields,
  getAllSourceFields,
} from "../api";
import { useLogTranslationQuery, useLogTranslator } from "./LogTranslation";

function useCustomFields(repoId: string) {
  const actorCustomFieldListQuery = useQuery({
    queryKey: ["logActorCustomFields", repoId],
    queryFn: () => getAllActorCustomFields(repoId),
    enabled: !!repoId,
  });
  const resourceCustomFieldListQuery = useQuery({
    queryKey: ["logResourceCustomFields", repoId],
    queryFn: () => getAllResourceCustomFields(repoId),
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
    actorCustomFields: actorCustomFieldListQuery.data ?? [],
    resourceCustomFields: resourceCustomFieldListQuery.data ?? [],
    detailFields: detailFieldListQuery.data ?? [],
    sourceFields: sourceFieldListQuery.data ?? [],
    loading:
      actorCustomFieldListQuery.isPending ||
      resourceCustomFieldListQuery.isPending ||
      detailFieldListQuery.isPending ||
      sourceFieldListQuery.isPending,
  };
}

export function useLogFields(
  repoId: string,
  mode: "search" | "columns",
  disabledFields?: Set<string>,
) {
  const { t } = useTranslation();
  const logTranslator = useLogTranslator(repoId);
  const logTranslationQuery = useLogTranslationQuery(repoId);
  const {
    actorCustomFields,
    resourceCustomFields,
    detailFields,
    sourceFields,
    loading: customFieldsLoading,
  } = useCustomFields(repoId);

  const item = (value: string, label?: string) => ({
    value,
    label: label ?? t(`log.${value}`),
    disabled: disabledFields && disabledFields.has(value),
  });

  return {
    fields: [
      { group: "Date", items: [item("savedAt", "Date")] },
      {
        group: "Action",
        items: [
          ...(mode === "columns"
            ? [item("action", t("log.action") + " *")]
            : []),
          item("actionCategory"),
          item("actionType"),
        ],
      },
      {
        group: "Actor",
        items: [
          ...(mode === "columns" ? [item("actor", t("log.actor") + " *")] : []),
          item("actorType"),
          ...(mode === "columns" ? [item("actorName")] : []),
          item("actorRef"),
          ...actorCustomFields.map((field) =>
            item(
              `actor.${field}`,
              t("log.actor") +
                ": " +
                logTranslator("actor_custom_field", field),
            ),
          ),
        ],
      },
      {
        group: t("log.source"),
        items: sourceFields.map((field) =>
          item(`source.${field}`, logTranslator("source_field", field)),
        ),
      },
      {
        group: t("log.resource"),
        items: [
          ...(mode === "columns"
            ? [item("resource", t("log.resource") + " *")]
            : []),
          item("resourceType"),
          ...(mode === "columns" ? [item("resourceName")] : []),
          item("resourceRef"),
          ...resourceCustomFields.map((field) =>
            item(
              `resource.${field}`,
              t("log.resource") +
                ": " +
                logTranslator("resource_custom_field", field),
            ),
          ),
        ],
      },
      {
        group: t("log.details"),
        items: detailFields.map((field) =>
          item(`details.${field}`, logTranslator("detail_field", field)),
        ),
      },
      {
        group: t("log.tag"),
        items: [
          ...(mode === "columns" ? [item("tag", t("log.tag") + " *")] : []),
          item("tagType"),
          ...(mode === "columns" ? [item("tagName")] : []),
          item("tagRef"),
        ],
      },
      {
        group: "Attachment",
        items: [
          ...(mode === "columns"
            ? [item("attachment", t("log.attachment") + " *")]
            : []),
          ...(mode === "search" ? [item("hasAttachment")] : []),
          item("attachmentName"),
          item("attachmentType"),
          item("attachmentMimeType"),
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

export function useLogFieldNames(
  repoId: string,
  mode: "search" | "columns",
  disabledFields?: Set<string>,
) {
  const { fields, loading } = useLogFields(repoId, mode, disabledFields);
  return loading
    ? null
    : fields.map((group) => group.items.map((item) => item.value)).flat();
}
