import { useDisclosure } from "@mantine/hooks";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { getAllLogEntities } from "@/features/log/api";
import { EntitySelector } from "@/features/log/components/EntitySelector";
import { LogSearchParams } from "@/features/log/LogSearchParams";
import { FIXED_SEARCH_PARAM_NAMES } from "./SearchParamFields";
import { SearchParamFieldPopover } from "./SearchParamFieldPopover";

export function EntitySearchParamField({
  searchParams,
  openedByDefault,
  onChange,
  onRemove,
}: {
  searchParams: LogSearchParams;
  openedByDefault: boolean;
  onChange: (name: string, value: any) => void;
  onRemove: (name: string) => void;
}) {
  const { t } = useTranslation();
  const logEntitiesQuery = useQuery({
    queryKey: ["logEntities", searchParams.repoId],
    queryFn: () => getAllLogEntities(searchParams.repoId),
    enabled: !!searchParams.repoId,
  });
  const [opened, { toggle }] = useDisclosure(openedByDefault);
  return (
    <SearchParamFieldPopover
      title={t("log.entity")}
      opened={opened}
      isSet={!!searchParams.entityRef}
      onChange={toggle}
      removable={!FIXED_SEARCH_PARAM_NAMES.has("entity")}
      onRemove={() => onRemove("entity")}
      loading={logEntitiesQuery.isPending}
    >
      <EntitySelector
        repoId={searchParams.repoId || null}
        entityRef={searchParams.entityRef}
        onChange={(value) => onChange("entityRef", value)}
      />
    </SearchParamFieldPopover>
  );
}

