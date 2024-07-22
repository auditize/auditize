import { useDocumentTitle } from "@mantine/hooks";
import { IconArchive } from "@tabler/icons-react";
import { useTranslation } from "react-i18next";

import { ResourceManagement } from "@/components/ResourceManagement";

import { getLogFilters, LogFilter } from "../api";
import { LogFilterDeletion } from "./LogFilterDeletion";
import { LogFilterEdition } from "./LogFilterEditor";

export function LogFilterManagement() {
  const { t } = useTranslation();
  useDocumentTitle(t("log.filter.filters"));

  return (
    <ResourceManagement
      title={
        <>
          <IconArchive />
          {t("log.filter.list.title")}
        </>
      }
      name={t("log.filter.filter")}
      resourceName="logFilter"
      stateMode="useState"
      queryKey={(search, page) => ["logFilters", search, page]}
      queryFn={(search, page) => () => getLogFilters(search, page)}
      columnBuilders={[
        [t("log.filter.list.column.name"), (filter: LogFilter) => filter.name],
      ]}
      resourceEditionComponentBuilder={(resourceId, onClose) => (
        <LogFilterEdition filterId={resourceId} onClose={onClose} />
      )}
      resourceDeletionComponentBuilder={(resource, opened, onClose) => (
        <LogFilterDeletion
          filter={resource}
          opened={opened}
          onClose={onClose}
        />
      )}
    />
  );
}
