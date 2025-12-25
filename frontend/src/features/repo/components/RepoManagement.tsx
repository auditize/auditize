import {
  Anchor,
  Code,
  CopyButton,
  Tooltip,
  UnstyledButton,
} from "@mantine/core";
import { useDocumentTitle } from "@mantine/hooks";
import { IconArchive, IconInfinity } from "@tabler/icons-react";
import { filesize } from "filesize";
import { useTranslation } from "react-i18next";
import { NavLink } from "react-router-dom";

import { DateTime } from "@/components/DateTime";
import { ResourceManagement } from "@/components/ResourceManagement";
import { useAuthenticatedUser } from "@/features/auth";
import { iconBesideText } from "@/utils/ui";

import { getRepos, Repo, useLogRepoListQuery } from "../api";
import { RepoDeletion } from "./RepoDeletion";
import { RepoCreation, RepoEdition } from "./RepoEditor";

function RepoName({ repo }: { repo: Repo }) {
  const { t } = useTranslation();
  const query = useLogRepoListQuery();

  const isAvailableForLogView = query.data?.some((r) => r.id === repo.id);
  if (isAvailableForLogView) {
    return (
      <Tooltip label={t("repo.list.column.viewLogs")} withArrow>
        <Anchor
          component={NavLink}
          to={`/logs?repoId=${repo.id}`}
          onClick={(event) => {
            event.stopPropagation();
          }}
          size="sm"
        >
          {repo.name}
        </Anchor>
      </Tooltip>
    );
  } else {
    return repo.name;
  }
}

function RepoId({ repo }: { repo: Repo }) {
  const { t } = useTranslation();

  return (
    <CopyButton value={repo.id} timeout={2000}>
      {({ copied, copy }) => (
        <Tooltip
          label={copied ? t("common.copied") : t("common.copy")}
          withArrow
          position="bottom"
        >
          <UnstyledButton
            onClick={(event) => {
              copy();
              event.stopPropagation();
            }}
          >
            <Code>{repo.id}</Code>
          </UnstyledButton>
        </Tooltip>
      )}
    </CopyButton>
  );
}

export function RepoManagement() {
  const { currentUser } = useAuthenticatedUser();
  const { t } = useTranslation();
  const readOnly = currentUser.permissions.management.repos.write === false;
  useDocumentTitle(t("repo.repos"));

  return (
    <ResourceManagement
      title={
        <>
          <IconArchive
            style={iconBesideText({
              size: "26",
              top: "4px",
              marginRight: "0.25rem",
            })}
          />
          {t("repo.list.title")}
        </>
      }
      name={t("repo.repo")}
      emptyStateMessage={t("repo.list.emptyStateMessage")}
      queryKey={(search, page) => [
        "repos",
        "list",
        search,
        page,
        { includeStats: true },
      ]}
      queryFn={(search, page) => () =>
        getRepos(search, page, { includeStats: true })
      }
      columnDefinitions={[
        [t("repo.list.column.name"), (repo: Repo) => <RepoName repo={repo} />],
        [t("repo.list.column.id"), (repo: Repo) => <RepoId repo={repo} />],
        [
          t("repo.list.column.status"),
          (repo: Repo) => t("repo.form.status.value." + repo.status),
        ],
        [
          t("repo.list.column.retentionPeriod"),
          (repo: Repo) =>
            repo.retentionPeriod ? (
              t("repo.list.column.retentionPeriodValue", {
                days: repo.retentionPeriod,
              })
            ) : (
              <IconInfinity
                stroke={1.5}
                style={{
                  position: "relative",
                  top: "1px",
                }}
              />
            ),
          { textAlign: "right", fontVariantNumeric: "tabular-nums" },
        ],
        [
          t("repo.list.column.logs"),
          (repo: Repo) => repo.stats!.logCount.toLocaleString(),
          { textAlign: "right", fontVariantNumeric: "tabular-nums" },
        ],
        [
          t("repo.list.column.storage"),
          (repo: Repo) => filesize(repo.stats!.storageSize, { round: 0 }),
          { textAlign: "right", fontVariantNumeric: "tabular-nums" },
        ],
        [
          t("common.createdAt"),
          (repo: Repo) => <DateTime value={repo.createdAt} />,
          { textAlign: "right", fontVariantNumeric: "tabular-nums" },
        ],
        [
          t("repo.list.column.lastLog"),
          (repo: Repo) =>
            repo.stats!.lastLogDate ? (
              <DateTime value={repo.stats!.lastLogDate} />
            ) : (
              <i>n/a</i>
            ),
          { textAlign: "right", fontVariantNumeric: "tabular-nums" },
        ],
      ]}
      resourceCreationComponentBuilder={
        readOnly
          ? undefined
          : (opened, onClose) => (
              <RepoCreation opened={opened} onClose={onClose} />
            )
      }
      resourceEditionComponentBuilder={(resourceId, onClose) => (
        <RepoEdition
          repoId={resourceId}
          onClose={onClose}
          readOnly={readOnly}
        />
      )}
      resourceDeletionComponentBuilder={(resource, opened, onClose) =>
        readOnly ? undefined : (
          <RepoDeletion repo={resource} opened={opened} onClose={onClose} />
        )
      }
    />
  );
}
