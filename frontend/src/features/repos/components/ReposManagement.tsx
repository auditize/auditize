import { Code, CopyButton, Tooltip, UnstyledButton } from "@mantine/core";
import { useDocumentTitle } from "@mantine/hooks";
import { IconArchive } from "@tabler/icons-react";
import { filesize } from "filesize";

import { ResourceManagement } from "@/components/ResourceManagement";
import { useAuthenticatedUser } from "@/features/auth";
import { humanizeDate } from "@/utils/date";

import { getRepos, Repo } from "../api";
import { RepoDeletion } from "./RepoDeletion";
import { RepoCreation, RepoEdition } from "./RepoEditor";

function RepoId({ value }: { value: string }) {
  return (
    <CopyButton value={value} timeout={2000}>
      {({ copied, copy }) => (
        <Tooltip label={copied ? "Copied" : "Copy"} withArrow position="bottom">
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
  const readOnly = currentUser.permissions.management.repos.write === false;
  useDocumentTitle("Repositories");

  return (
    <ResourceManagement
      title={
        <>
          <IconArchive />
          Repositories
        </>
      }
      name="Repository"
      path="/repos"
      resourceName="repo"
      queryKey={(page) => ["repos", "page", page, { includeStats: true }]}
      queryFn={(page) => () => getRepos(page, { includeStats: true })}
      columnBuilders={[
        ["Name", (repo: Repo) => repo.name],
        ["ID", (repo: Repo) => <RepoId value={repo.id} />],
        ["Logs", (repo: Repo) => repo.stats!.logCount.toLocaleString()],
        ["Storage", (repo: Repo) => filesize(repo.stats!.storageSize)],
        ["Created", (repo: Repo) => humanizeDate(repo.createdAt)],
        [
          "Last log",
          (repo: Repo) => humanizeDate(repo.stats!.lastLogDate) || "n/a",
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
