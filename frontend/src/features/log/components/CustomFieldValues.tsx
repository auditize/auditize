import { CodeHighlight } from "@mantine/code-highlight";
import { useTranslation } from "react-i18next";

import { CustomField, CustomFieldType } from "@/features/log/api";

import { useCustomFieldEnumValueTranslator } from "./LogTranslation";

function EnumFieldValue({
  repoId,
  field,
  fieldCategoryKey,
}: {
  repoId: string;
  field: CustomField;
  fieldCategoryKey: string;
}) {
  const translator = useCustomFieldEnumValueTranslator(repoId);

  return translator(fieldCategoryKey, field.name, field.value);
}

function BooleanFieldValue({ field }: { field: CustomField }) {
  const { t } = useTranslation();

  return t(`common.${field.value ? "yes" : "no"}`);
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
  fieldCategoryKey,
}: {
  repoId: string;
  field: CustomField;
  fieldCategoryKey: string;
}) {
  if (field.type === CustomFieldType.Boolean) {
    return <BooleanFieldValue field={field} />;
  }
  if (field.type === CustomFieldType.Json) {
    return <JsonFieldValue field={field} />;
  }
  if (field.type === CustomFieldType.Enum) {
    return (
      <EnumFieldValue
        repoId={repoId}
        field={field}
        fieldCategoryKey={fieldCategoryKey}
      />
    );
  }
  return field.value;
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
      fieldCategoryKey="detail_field"
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
      fieldCategoryKey="resource_custom_field"
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
      fieldCategoryKey="actor_custom_field"
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
      fieldCategoryKey="source_field"
    />
  );
}
