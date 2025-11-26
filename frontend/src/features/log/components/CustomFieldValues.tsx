import { CodeHighlight } from "@mantine/code-highlight";
import { useTranslation } from "react-i18next";

import { CustomField, CustomFieldType } from "@/features/log/api";

import { useCustomFieldEnumValueTranslator } from "./LogTranslation";

function useCustomFieldValueTranslator(
  repoId: string | undefined,
  fieldType: string,
) {
  const { t } = useTranslation();
  const enumTranslator = useCustomFieldEnumValueTranslator(repoId);

  return (field: CustomField) => {
    if (field.type === CustomFieldType.Enum) {
      return enumTranslator(fieldType, field.name, field.value);
    } else if (field.type === CustomFieldType.Boolean) {
      return t(`common.${field.value ? "yes" : "no"}`);
    }
    return field.value;
  };
}

function JsonFieldValue({ field }: { field: CustomField }) {
  const { t } = useTranslation();
  let formattedJson = field.value;
  try {
    const parsed = JSON.parse(field.value);
    formattedJson = JSON.stringify(parsed, null, 2);
  } catch {
    // ignore
  }
  return (
    <CodeHighlight
      code={formattedJson}
      language="json"
      withExpandButton
      defaultExpanded={false}
      collapseCodeLabel={t("common.lessDetails")}
      expandCodeLabel={t("common.moreDetails")}
      copyLabel={t("common.copy")}
      copiedLabel={t("common.copied")}
      styles={{
        code: { padding: "5px 8px 5px 8px" },
        scrollarea: { maxWidth: "400px" },
      }}
    />
  );
}

export function CustomFieldValue({
  repoId,
  field,
  fieldTypeKey,
}: {
  repoId: string;
  field: CustomField;
  fieldTypeKey: string;
}) {
  const translator = useCustomFieldValueTranslator(repoId, fieldTypeKey);
  if (field.type === CustomFieldType.Json) {
    return <JsonFieldValue field={field} />;
  }
  return translator(field);
}

export function DetailFieldValue({
  repoId,
  field,
}: {
  repoId: string;
  field: CustomField;
}) {
  return (
    <CustomFieldValue
      repoId={repoId}
      field={field}
      fieldTypeKey="detail_field"
    />
  );
}

export function ResourceExtraFieldValue({
  repoId,
  field,
}: {
  repoId: string;
  field: CustomField;
}) {
  return (
    <CustomFieldValue
      repoId={repoId}
      field={field}
      fieldTypeKey="resource_custom_field"
    />
  );
}

export function ActorExtraFieldValue({
  repoId,
  field,
}: {
  repoId: string;
  field: CustomField;
}) {
  return (
    <CustomFieldValue
      repoId={repoId}
      field={field}
      fieldTypeKey="actor_custom_field"
    />
  );
}

export function SourceFieldValue({
  repoId,
  field,
}: {
  repoId: string;
  field: CustomField;
}) {
  return (
    <CustomFieldValue
      repoId={repoId}
      field={field}
      fieldTypeKey="source_field"
    />
  );
}

