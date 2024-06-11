import { Code, CopyButton, Tooltip, UnstyledButton } from "@mantine/core";
import { useDocumentTitle } from "@mantine/hooks";
import { IconArchive } from "@tabler/icons-react";
import { filesize } from "filesize";
import { useTranslation } from "react-i18next";

import { ResourceManagement } from "@/components/ResourceManagement";
import { useAuthenticatedUser } from "@/features/auth";
import { humanizeDate } from "@/utils/date";

import { getRepos, Repo } from "../api";
import { RepoDeletion } from "./RepoDeletion";
import { RepoCreation, RepoEdition } from "./RepoEditor";

function RepoId({ value }: { value: string }) {
  const { t } = useTranslation();

  return (
    <CopyButton value={value} timeout={2000}>
      {({ copied, copy }) => (
        <Tooltip
          label={copied ? t("common.copied") : t("common.copy")}
          withArrow
          position="bottom"
        >
          <UnstyledButton onClick={copy}>
            <Code>{value}</Code>
          </UnstyledButton>
        </Tooltip>
      )}
    </CopyButton>
  );
}

export function ReposManagement() {
  const { currentUser } = useAuthenticatedUser();
  const { t } = useTranslation();
  const readOnly = currentUser.permissions.management.repos.write === false;
  useDocumentTitle(t("repo.repos"));

  return (
    <ResourceManagement
      title={
        <>
          <IconArchive />
          {t("repo.list.title")}
        </>
      }
      name={t("repo.repo")}
      path="/repos"
      resourceName="repo"
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
      columnBuilders={[
        [t("repo.list.column.name"), (repo: Repo) => repo.name],
        [t("repo.list.column.id"), (repo: Repo) => <RepoId value={repo.id} />],
        [t("repo.list.column.status"), (repo: Repo) => repo.status],
        [
          t("repo.list.column.logs"),
          (repo: Repo) => repo.stats!.logCount.toLocaleString(),
        ],
        [
          t("repo.list.column.storage"),
          (repo: Repo) => filesize(repo.stats!.storageSize),
        ],
        [
          t("repo.list.column.createdAt"),
          (repo: Repo) => humanizeDate(repo.createdAt),
        ],
        [
          t("repo.list.column.lastLog"),
          (repo: Repo) =>
            repo.stats!.lastLogDate
              ? humanizeDate(repo.stats!.lastLogDate)
              : "n/a",
        ],
      ]}
      resourceCreationComponentBuilder={
        readOnly ? undefined : (opened) => <RepoCreation opened={opened} />
      }
      resourceEditionComponentBuilder={(resourceId) => (
        <RepoEdition repoId={resourceId} readOnly={readOnly} />
      )}
      resourceDeletionComponentBuilder={(resource, opened, onClose) =>
        readOnly ? undefined : (
          <RepoDeletion repo={resource} opened={opened} onClose={onClose} />
        )
      }
    />
  );
}
