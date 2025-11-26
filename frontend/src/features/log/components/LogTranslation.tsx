import { CodeHighlight } from "@mantine/code-highlight";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { CustomField, CustomFieldType } from "@/features/log/api";
import { getRepoTranslation } from "@/features/repo";
import { useI18nContext } from "@/i18n";
import { titlize } from "@/utils/format";

export function useLogTranslationQuery(repoId?: string) {
  const { lang } = useI18nContext();
  return useQuery({
    queryKey: ["logTranslation", repoId, lang],
    queryFn: () => getRepoTranslation(repoId!, lang),
    enabled: !!repoId,
  });
}

export function useLogTranslator(repoId?: string) {
  const translationQuery = useLogTranslationQuery(repoId);

  return (fieldType: string, fieldName: string) => {
    const defaultTranslation = titlize(fieldName);
    if (!translationQuery.data) {
      return defaultTranslation;
    }
    return translationQuery.data[fieldType]?.[fieldName] || defaultTranslation;
  };
}

export function useCustomFieldEnumValueTranslator(repoId?: string) {
  const translationQuery = useLogTranslationQuery(repoId);

  return (fieldType: string, fieldName: string, enumValue: string) => {
    const defaultTranslation = titlize(enumValue);
    if (!translationQuery.data) {
      return defaultTranslation;
    }
    return (
      translationQuery.data[fieldType + "_enum_value"]?.[fieldName]?.[enumValue] || defaultTranslation // prettier-ignore
    );
  };
}

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
