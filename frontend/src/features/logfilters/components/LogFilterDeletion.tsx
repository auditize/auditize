import { Trans, useTranslation } from "react-i18next";

import { ResourceDeletion } from "@/components/ResourceManagement";

import { deleteLogFilter, LogFilter } from "../api";

export function LogFilterDeletion({
  filter,
  opened,
  onClose,
}: {
  filter: LogFilter;
  opened: boolean;
  onClose: () => void;
}) {
  const { t } = useTranslation();
  return (
    <ResourceDeletion
      message={
        <Trans
          i18nKey="log.filter.delete.confirm"
          values={{ name: filter.name }}
        >
          Do you confirm the deletion of filter <b>{filter.name}</b> ?
        </Trans>
      }
      opened={opened}
      onDelete={() => deleteLogFilter(filter.id)}
      queryKeyForInvalidation={["logFilters"]}
      onClose={onClose}
    />
  );
}
