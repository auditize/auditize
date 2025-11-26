import { useQuery } from "@tanstack/react-query";

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
