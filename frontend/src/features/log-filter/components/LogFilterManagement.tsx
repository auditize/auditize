import { Anchor, rem, Tooltip } from "@mantine/core";
import { useDocumentTitle } from "@mantine/hooks";
import { IconFilter, IconStar, IconStarFilled } from "@tabler/icons-react";
import { useTranslation } from "react-i18next";
import { NavLink } from "react-router-dom";

import { ResourceManagement } from "@/components/ResourceManagement";
import { iconBesideText } from "@/utils/ui";

import { getLogFilters, LogFilter } from "../api";
import { LogFilterDeletion } from "./LogFilterDeletion";
import { LogFilterEdition } from "./LogFilterEditor";

function FavoriteIcon({
  value,
  style,
}: {
  value: boolean;
  style?: React.CSSProperties;
}) {
  return value ? (
    <IconStarFilled style={style} color="var(--mantine-color-yellow-3)" />
  ) : (
    <IconStar style={style} color="var(--mantine-color-gray-3)" />
  );
}

export function LogFilterManagement() {
  const { t } = useTranslation();
  useDocumentTitle(t("log.filter.filters"));

  return (
    <ResourceManagement
      title={
        <>
          <IconFilter
            style={iconBesideText({
              size: "26",
              top: "4px",
              marginRight: "0.25rem",
            })}
          />
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
            <>
              <FavoriteIcon
                value={filter.isFavorite}
                style={iconBesideText({
                  size: "18",
                  top: "3px",
                  marginRight: rem(8),
                })}
              />
              <Tooltip label={t("log.filter.list.apply")} withArrow>
                <Anchor
                  component={NavLink}
                  to={`/logs?filterId=${filter.id}`}
                  onClick={(e) => e.stopPropagation()}
                >
                  {filter.name}
                </Anchor>
              </Tooltip>
            </>
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
