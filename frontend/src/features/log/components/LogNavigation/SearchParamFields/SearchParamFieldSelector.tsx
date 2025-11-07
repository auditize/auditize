import { ActionIcon, Tooltip, useCombobox } from "@mantine/core";
import { IconPlus } from "@tabler/icons-react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { CustomMultiSelect } from "@/components/CustomMultiSelect";
import {
  getAllActionCategories,
  getAllActionTypes,
  getAllActorTypes,
  getAllAttachmentMimeTypes,
  getAllAttachmentTypes,
  getAllLogEntities,
  getAllResourceTypes,
  getAllTagTypes,
} from "@/features/log/api";
import { useSearchFields } from "@/features/log/components/useLogFields";

import { FIXED_SEARCH_PARAM_NAMES } from "./SearchParamFields";

export function useLogConsolidatedDataPrefetch(repoId: string) {
  const actionCategoriesQuery = useQuery({
    queryKey: ["logConsolidatedData", "actionCategory", repoId],
    queryFn: () => getAllActionCategories(repoId),
    enabled: !!repoId,
  });
  const actionTypesQuery = useQuery({
    queryKey: ["logConsolidatedData", "actionType", repoId],
    queryFn: () => getAllActionTypes(repoId),
    enabled: !!repoId,
  });
  const actorTypesQuery = useQuery({
    queryKey: ["logConsolidatedData", "actorType", repoId],
    queryFn: () => getAllActorTypes(repoId),
    enabled: !!repoId,
  });
  const resourceTypesQuery = useQuery({
    queryKey: ["logConsolidatedData", "resourceType", repoId],
    queryFn: () => getAllResourceTypes(repoId),
    enabled: !!repoId,
  });
  const tagTypesQuery = useQuery({
    queryKey: ["logConsolidatedData", "tagType", repoId],
    queryFn: () => getAllTagTypes(repoId),
    enabled: !!repoId,
  });
  const attachmentTypesQuery = useQuery({
    queryKey: ["logConsolidatedData", "attachmentType", repoId],
    queryFn: () => getAllAttachmentTypes(repoId),
    enabled: !!repoId,
  });
  const attachmentMimeTypesQuery = useQuery({
    queryKey: ["logConsolidatedData", "attachmentMimeType", repoId],
    queryFn: () => getAllAttachmentMimeTypes(repoId),
    enabled: !!repoId,
  });
  const logEntitiesQuery = useQuery({
    queryKey: ["logEntities", repoId],
    queryFn: () => getAllLogEntities(repoId),
    enabled: !!repoId,
  });
  return (
    actionCategoriesQuery.isPending ||
    actionTypesQuery.isPending ||
    actorTypesQuery.isPending ||
    resourceTypesQuery.isPending ||
    tagTypesQuery.isPending ||
    attachmentTypesQuery.isPending ||
    attachmentMimeTypesQuery.isPending ||
    logEntitiesQuery.isPending
  );
}

export function SearchParamFieldSelector({
  repoId,
  selected,
  onSearchParamAdded,
  onSearchParamRemoved,
}: {
  repoId: string;
  selected: Set<string>;
  onSearchParamAdded: (name: string) => void;
  onSearchParamRemoved: (name: string) => void;
}) {
  const { fields, loading: logFieldsLoading } = useSearchFields(
    repoId,
    FIXED_SEARCH_PARAM_NAMES,
  );
  const logConsolidatedDataLoading = useLogConsolidatedDataPrefetch(repoId);
  const comboboxStore = useCombobox();
  const { t } = useTranslation();

  return (
    <CustomMultiSelect
      comboboxStore={comboboxStore}
      data={fields}
      value={Array.from(selected)}
      onOptionSubmit={onSearchParamAdded}
      onRemove={onSearchParamRemoved}
      closeOnSelect
    >
      <Tooltip
        label={t("log.list.searchParams.more")}
        disabled={comboboxStore.dropdownOpened}
        position="bottom"
        withArrow
        withinPortal={false}
      >
        <ActionIcon
          onClick={() => comboboxStore.toggleDropdown()}
          loading={logFieldsLoading || logConsolidatedDataLoading}
          loaderProps={{ type: "dots" }}
          size="input-sm"
        >
          <IconPlus />
        </ActionIcon>
      </Tooltip>
    </CustomMultiSelect>
  );
}
