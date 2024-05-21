import { IconArchive } from "@tabler/icons-react";
import { filesize } from "filesize";

import { ResourceManagement } from "@/components/ResourceManagement";
import { useAuthenticatedUser } from "@/features/auth";
import { humanizeDate } from "@/utils/date";

import { getRepos, Repo } from "../api";
import { RepoDeletion } from "./RepoDeletion";
import { RepoCreation, RepoEdition } from "./RepoEditor";

export function ReposManagement() {
  const { currentUser } = useAuthenticatedUser();
  const readOnly = currentUser.permissions.management.repos.write === false;

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
        ["Creation date", (repo: Repo) => humanizeDate(repo.createdAt)],
        [
          "Last log date",
          (repo: Repo) => humanizeDate(repo.stats!.lastLogDate) || "n/a",
        ],
        ["Logs", (repo: Repo) => repo.stats!.logCount.toLocaleString()],
        ["Storage size", (repo: Repo) => filesize(repo.stats!.storageSize)],
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
