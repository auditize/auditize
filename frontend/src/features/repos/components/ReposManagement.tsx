import { ResourceManagement } from "@/components/ResourceManagement";
import { useAuthenticatedUser } from "@/features/auth";

import { getRepos } from "../api";
import { RepoDeletion } from "./RepoDeletion";
import { RepoCreation, RepoEdition } from "./RepoEditor";

export function ReposManagement() {
  const { currentUser } = useAuthenticatedUser();
  const readOnly = currentUser.permissions.management.repos.write === false;

  return (
    <ResourceManagement
      title="Repos Management"
      path="/repos"
      resourceName="repo"
      queryKey={(page) => ["repos", "page", page, { includeStats: true }]}
      queryFn={(page) => () => getRepos(page, { includeStats: true })}
      columnBuilders={[
        ["Name", (repo: Repo) => repo.name],
        ["Creation date", (repo: Repo) => repo.created_at],
        ["First log date", (repo: Repo) => repo.stats!.first_log_date || "n/a"],
        ["Last log date", (repo: Repo) => repo.stats!.last_log_date || "n/a"],
        ["Log count", (repo: Repo) => repo.stats!.log_count],
        ["Storage size", (repo: Repo) => repo.stats!.storage_size],
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
