import { Anchor } from "@mantine/core";
import { useDocumentTitle } from "@mantine/hooks";
import { IconArchive } from "@tabler/icons-react";
import { useTranslation } from "react-i18next";
import { NavLink } from "react-router-dom";

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
      stateMode="useState"
      queryKey={(search, page) => ["logFilters", search, page]}
      queryFn={(search, page) => () => getLogFilters(search, page)}
      columnDefinitions={[
        [
          t("log.filter.list.column.name"),
          (filter: LogFilter) => (
            <Anchor component={NavLink} to={`/logs?filterId=${filter.id}`}>
              {filter.name}
            </Anchor>
          ),
        ],
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
