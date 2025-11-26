import { useQuery } from "@tanstack/react-query";

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

export function useCustomFieldValueTranslator(
  repoId: string | undefined,
  fieldType: string,
) {
  const enumTranslator = useCustomFieldEnumValueTranslator(repoId);

  return (field: CustomField) => {
    if (field.type === CustomFieldType.Enum) {
      return enumTranslator(fieldType, field.name, field.value);
    }
    return field.value;
  };
}

export function DetailFieldValue({
  repoId,
  field,
}: {
  repoId: string;
  field: CustomField;
}) {
  const translator = useCustomFieldValueTranslator(repoId, "detail_field");
  return translator(field);
}

export function ResourceExtraFieldValue({
  repoId,
  field,
}: {
  repoId: string;
  field: CustomField;
}) {
  const translator = useCustomFieldValueTranslator(
    repoId,
    "resource_custom_field",
  );
  return translator(field);
}

export function ActorExtraFieldValue({
  repoId,
  field,
}: {
  repoId: string;
  field: CustomField;
}) {
  const translator = useCustomFieldValueTranslator(
    repoId,
    "actor_custom_field",
  );
  return translator(field);
}

export function SourceFieldValue({
  repoId,
  field,
}: {
  repoId: string;
  field: CustomField;
}) {
  const translator = useCustomFieldValueTranslator(repoId, "source_field");
  return translator(field);
}
