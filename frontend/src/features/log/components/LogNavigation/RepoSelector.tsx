import { Select } from "@mantine/core";
import { useTranslation } from "react-i18next";

import { useLogRepoListQuery } from "@/features/repo";

export function RepoSelector({
  repoId,
  onChange,
}: {
  repoId?: string;
  onChange: (value: string) => void;
}) {
  const { t } = useTranslation();
  const query = useLogRepoListQuery();

  return (
    <Select
      data={query.data?.map((repo) => ({
        label: repo.name,
        value: repo.id,
      }))}
      value={repoId || null}
      onChange={(value) => onChange(value || "")}
      placeholder={
        query.error
          ? t("common.notCurrentlyAvailable")
          : query.isPending
            ? t("common.loading")
            : undefined
      }
      disabled={query.isPending}
      clearable={false}
      allowDeselect={false}
      display="flex"
      comboboxProps={{ withinPortal: false, shadow: "md" }}
    />
  );
}
