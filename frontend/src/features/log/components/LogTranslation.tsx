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
    const defaultFieldTranslation = titlize(fieldName);
    if (!translationQuery.data) {
      return defaultFieldTranslation;
    }
    return (
      translationQuery.data[fieldType]?.[fieldName] || defaultFieldTranslation
    );
  };
}
