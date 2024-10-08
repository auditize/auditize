import { useQuery } from "@tanstack/react-query";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";

import {
  getAllLogActorCustomFields,
  getAllLogDetailFields,
  getAllLogResourceCustomFields,
  getAllLogSourceFields,
} from "../api";
import { useLogTranslationQuery, useLogTranslator } from "./LogTranslation";

export function useLogFields(
  repoId: string,
  mode: "search" | "columns",
  disabledFields?: Set<string>,
) {
  const { t } = useTranslation();
  const logTranslator = useLogTranslator(repoId);
  const actorCustomFieldListQuery = useQuery({
    queryKey: ["logActorCustomFields", repoId],
    queryFn: () => getAllLogActorCustomFields(repoId),
    enabled: !!repoId,
  });
  const resourceCustomFieldListQuery = useQuery({
    queryKey: ["logResourceCustomFields", repoId],
    queryFn: () => getAllLogResourceCustomFields(repoId),
    enabled: !!repoId,
  });
  const detailFieldListQuery = useQuery({
    queryKey: ["logDetailFields", repoId],
    queryFn: () => getAllLogDetailFields(repoId),
    enabled: !!repoId,
  });
  const sourceFieldListQuery = useQuery({
    queryKey: ["logSourceFields", repoId],
    queryFn: () => getAllLogSourceFields(repoId),
    enabled: !!repoId,
  });
  const logTranslationQuery = useLogTranslationQuery(repoId);

  const _ = ({ value, label }: { value: string; label: string }) => ({
    value,
    label,
    disabled: disabledFields && disabledFields.has(value),
  });

  return {
    fields: [
      { group: "Date", items: [_({ value: "savedAt", label: "Date" })] },
      {
        group: "Action",
        items: [
          ...(mode === "columns"
            ? [_({ value: "action", label: t("log.action") + " *" })]
            : []),
          _({ value: "actionCategory", label: t("log.actionCategory") }),
          _({ value: "actionType", label: t("log.actionType") }),
        ],
      },
      {
        group: "Actor",
        items: [
          ...(mode === "columns"
            ? [_({ value: "actor", label: t("log.actor") + " *" })]
            : []),
          _({ value: "actorType", label: t("log.actorType") }),
          _({ value: "actorName", label: t("log.actorName") }),
          _({ value: "actorRef", label: t("log.actorRef") }),
          ...(actorCustomFieldListQuery.data ?? []).map((field) =>
            _({
              value: `actor.${field}`,
              label:
                t("log.actor") +
                ": " +
                logTranslator("actor_custom_field", field),
            }),
          ),
        ],
      },
      {
        group: t("log.source"),
        items: (sourceFieldListQuery.data ?? []).map((field) =>
          _({
            value: `source.${field}`,
            label: logTranslator("source_field", field),
          }),
        ),
      },
      {
        group: t("log.resource"),
        items: [
          ...(mode === "columns"
            ? [_({ value: "resource", label: t("log.resource") + " *" })]
            : []),
          _({ value: "resourceType", label: t("log.resourceType") }),
          _({ value: "resourceName", label: t("log.resourceName") }),
          _({ value: "resourceRef", label: t("log.resourceRef") }),
          ...(resourceCustomFieldListQuery.data ?? []).map((field) =>
            _({
              value: `resource.${field}`,
              label:
                t("log.resource") +
                ": " +
                logTranslator("resource_custom_field", field),
            }),
          ),
        ],
      },
      {
        group: t("log.details"),
        items: (detailFieldListQuery.data ?? []).map((field) =>
          _({
            value: `details.${field}`,
            label: logTranslator("detail_field", field),
          }),
        ),
      },
      {
        group: t("log.tag"),
        items: [
          ...(mode === "columns"
            ? [_({ value: "tag", label: t("log.tag") + " *" })]
            : []),
          _({ value: "tagType", label: t("log.tagType") }),
          _({ value: "tagName", label: t("log.tagName") }),
          _({ value: "tagRef", label: t("log.tagRef") }),
        ],
      },
      {
        group: "Attachment",
        items: [
          ...(mode === "columns"
            ? [_({ value: "attachment", label: t("log.attachment") + " *" })]
            : []),
          ...(mode === "search"
            ? [_({ value: "hasAttachment", label: t("log.hasAttachment") })]
            : []),
          _({ value: "attachmentName", label: t("log.attachmentName") }),
          _({ value: "attachmentType", label: t("log.attachmentType") }),
          _({
            value: "attachmentMimeType",
            label: t("log.attachmentMimeType"),
          }),
        ],
      },
      {
        group: t("log.entity"),
        items: [_({ value: "entity", label: t("log.entity") })],
      },
    ],
    loading:
      actorCustomFieldListQuery.isPending ||
      resourceCustomFieldListQuery.isPending ||
      detailFieldListQuery.isPending ||
      sourceFieldListQuery.isPending ||
      logTranslationQuery.isPending,
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
