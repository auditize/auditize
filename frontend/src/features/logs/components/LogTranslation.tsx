import { useQuery } from "@tanstack/react-query";

import { useAuthenticatedUser } from "@/features/auth";
import { getRepoTranslation } from "@/features/repos";
import { titlize } from "@/utils/format";

export function useLogTranslationQuery(repoId?: string) {
  const { currentUser } = useAuthenticatedUser();
  return useQuery({
    // pass lang to queryKey to invalidate the query when the user changes the language
    queryKey: ["logTranslation", repoId, currentUser.lang],
    queryFn: () => getRepoTranslation(repoId!),
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
