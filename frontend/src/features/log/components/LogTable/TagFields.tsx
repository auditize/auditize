import { Badge, Breadcrumbs } from "@mantine/core";
import { useTranslation } from "react-i18next";

import { Log } from "@/features/log/api";
import { useLogTranslator } from "@/features/log/components/LogTranslation";

import {
  InlineSearchParamLink,
  TableSearchParamChangeHandler,
} from "./FieldUtils";

export function TagsField({
  log,
  repoId,
  onTableSearchParamChange,
}: {
  log: Log;
  repoId: string;
  onTableSearchParamChange: TableSearchParamChangeHandler;
}) {
  const { t } = useTranslation();
  const logTranslator = useLogTranslator(repoId);

  return (
    <Breadcrumbs separator={null} separatorMargin="0.250rem">
      {log.tags.map((tag, i) =>
        tag.ref ? (
          <InlineSearchParamLink
            fieldLabel={t("log.inlineFilter.field.tag")}
            onClick={() => onTableSearchParamChange("tagRef", tag.ref!)}
            key={i}
          >
            <Badge size="sm" variant="outline" style={{ cursor: "pointer" }}>
              {logTranslator("tag_type", tag.type) + ": " + tag.name}
            </Badge>
          </InlineSearchParamLink>
        ) : (
          <InlineSearchParamLink
            fieldLabel={t("log.inlineFilter.field.tag")}
            onClick={() => onTableSearchParamChange("tagType", tag.type)}
            key={i}
          >
            <Badge size="sm" variant="outline" style={{ cursor: "pointer" }}>
              {logTranslator("tag_type", tag.type)}
            </Badge>
          </InlineSearchParamLink>
        ),
      )}
    </Breadcrumbs>
  );
}

export function TagTypesField({
  log,
  repoId,
  onTableSearchParamChange,
}: {
  log: Log;
  repoId: string;
  onTableSearchParamChange: TableSearchParamChangeHandler;
}) {
  const { t } = useTranslation();
  const logTranslator = useLogTranslator(repoId);

  return (
    <Breadcrumbs separator=", ">
      {log.tags.map((tag, i) => (
        <InlineSearchParamLink
          fieldLabel={t("log.inlineFilter.field.tagType")}
          onClick={() => onTableSearchParamChange("tagType", tag.type)}
          key={i}
        >
          {logTranslator("tag_type", tag.type)}
        </InlineSearchParamLink>
      ))}
    </Breadcrumbs>
  );
}

export function TagNamesField({
  log,
  onTableSearchParamChange,
}: {
  log: Log;
  onTableSearchParamChange: TableSearchParamChangeHandler;
}) {
  const { t } = useTranslation();

  return (
    <Breadcrumbs separator=", ">
      {log.tags.map(
        (tag, i) =>
          tag.name && (
            <InlineSearchParamLink
              fieldLabel={t("log.inlineFilter.field.tagName")}
              onClick={() => onTableSearchParamChange("tagName", tag.name!)}
              key={i}
            >
              {tag.name}
            </InlineSearchParamLink>
          ),
      )}
    </Breadcrumbs>
  );
}

export function TagRefsField({
  log,
  onTableSearchParamChange,
}: {
  log: Log;
  onTableSearchParamChange: TableSearchParamChangeHandler;
}) {
  const { t } = useTranslation();

  return (
    <Breadcrumbs separator=", ">
      {log.tags.map(
        (tag, i) =>
          tag.ref && (
            <InlineSearchParamLink
              fieldLabel={t("log.inlineFilter.field.tagRef")}
              onClick={() => onTableSearchParamChange("tagRef", tag.ref!)}
              key={i}
            >
              {tag.ref}
            </InlineSearchParamLink>
          ),
      )}
    </Breadcrumbs>
  );
}
