import { Breadcrumbs } from "@mantine/core";
import { useTranslation } from "react-i18next";

import { Log } from "@/features/log/api";
import { useLogTranslator } from "@/features/log/components/LogTranslation";

import {
  InlineSearchParamLink,
  TableSearchParamChangeHandler,
} from "./FieldUtils";

export function AttachmentNamesField({
  log,
  onTableSearchParamChange,
}: {
  log: Log;
  onTableSearchParamChange: TableSearchParamChangeHandler;
}) {
  const { t } = useTranslation();

  return (
    <Breadcrumbs separator=", ">
      {log.attachments.map((attachment, i) => (
        <InlineSearchParamLink
          label={t("log.inlineFilter.field.attachmentName")}
          onClick={() =>
            onTableSearchParamChange("attachmentName", attachment.name)
          }
          key={i}
        >
          {attachment.name}
        </InlineSearchParamLink>
      ))}
    </Breadcrumbs>
  );
}

export function AttachmentTypesField({
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
      {log.attachments.map((attachment, i) => (
        <InlineSearchParamLink
          label={t("log.inlineFilter.field.attachmentType")}
          onClick={() =>
            onTableSearchParamChange("attachmentType", attachment.type)
          }
          key={i}
        >
          {logTranslator("attachment_type", attachment.type)}
        </InlineSearchParamLink>
      ))}
    </Breadcrumbs>
  );
}

export function AttachmentMimeTypesField({
  log,
  onTableSearchParamChange,
}: {
  log: Log;
  onTableSearchParamChange: TableSearchParamChangeHandler;
}) {
  const { t } = useTranslation();

  return (
    <Breadcrumbs separator=", ">
      {log.attachments.map((attachment, i) => (
        <InlineSearchParamLink
          label={t("log.inlineFilter.field.attachmentMimeType")}
          onClick={() =>
            onTableSearchParamChange("attachmentMimeType", attachment.mimeType)
          }
          key={i}
        >
          {attachment.mimeType}
        </InlineSearchParamLink>
      ))}
    </Breadcrumbs>
  );
}
