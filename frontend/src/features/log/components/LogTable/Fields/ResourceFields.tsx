import { useTranslation } from "react-i18next";

import { Log } from "@/features/log/api";
import { ResourceExtraFieldValue } from "@/features/log/components/CustomFieldValues";
import { useLogTranslator } from "@/features/log/components/LogTranslation";

import {
  getCustomField,
  InlineSearchParamLink,
  TableSearchParamChangeHandler,
} from "./FieldUtils";

export function ResourceField({
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

  return log.resource ? (
    <>
      <InlineSearchParamLink
        fieldLabel={t("log.inlineFilter.field.resourceType")}
        onClick={() =>
          onTableSearchParamChange("resourceType", log.resource!.type)
        }
      >
        {logTranslator("resource_type", log.resource.type)}
      </InlineSearchParamLink>
      {": "}
      <InlineSearchParamLink
        fieldLabel={t("log.inlineFilter.field.resource")}
        onClick={() =>
          onTableSearchParamChange("resourceRef", log.resource!.ref)
        }
        fontWeight="600"
      >
        {log.resource.name}
      </InlineSearchParamLink>
    </>
  ) : null;
}

export function ResourceTypeField({
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

  return log.resource ? (
    <InlineSearchParamLink
      fieldLabel={t("log.inlineFilter.field.resourceType")}
      onClick={() =>
        onTableSearchParamChange("resourceType", log.resource!.type)
      }
    >
      {logTranslator("resource_type", log.resource.type)}
    </InlineSearchParamLink>
  ) : null;
}

export function ResourceNameField({
  log,
  onTableSearchParamChange,
}: {
  log: Log;
  onTableSearchParamChange: TableSearchParamChangeHandler;
}) {
  const { t } = useTranslation();

  return log.resource ? (
    <InlineSearchParamLink
      fieldLabel={t("log.inlineFilter.field.resourceName")}
      onClick={() =>
        onTableSearchParamChange("resourceName", log.resource!.name)
      }
    >
      {log.resource.name}
    </InlineSearchParamLink>
  ) : null;
}

export function ResourceRefField({
  log,
  onTableSearchParamChange,
}: {
  log: Log;
  onTableSearchParamChange: TableSearchParamChangeHandler;
}) {
  const { t } = useTranslation();

  return log.resource ? (
    <InlineSearchParamLink
      fieldLabel={t("log.inlineFilter.field.resourceRef")}
      onClick={() => onTableSearchParamChange("resourceRef", log.resource!.ref)}
    >
      {log.resource.ref}
    </InlineSearchParamLink>
  ) : null;
}

export function ResourceCustomField({
  log,
  repoId,
  fieldName,
  onTableSearchParamChange,
}: {
  log: Log;
  repoId: string;
  fieldName: string;
  onTableSearchParamChange: TableSearchParamChangeHandler;
}) {
  const { t } = useTranslation();
  const logTranslator = useLogTranslator(repoId);
  const field = getCustomField(log.resource?.extra, fieldName);
  if (!field) {
    return null;
  }

  return (
    <InlineSearchParamLink
      fieldLabel={t("log.inlineFilter.field.resourceCustomField", {
        field: logTranslator("resource_custom_field", field.name).toLowerCase(),
      })}
      onClick={() =>
        onTableSearchParamChange(
          "resourceExtra",
          new Map([[field.name, field.value]]),
        )
      }
    >
      <ResourceExtraFieldValue repoId={repoId} field={field} />
    </InlineSearchParamLink>
  );
}
