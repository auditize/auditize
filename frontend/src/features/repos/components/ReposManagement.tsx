import { RepoCreation, RepoEdition } from './RepoEditor';
import { RepoDeletion } from './RepoDeletion';
import { getRepos } from '../api';
import { ResourceManagement } from '@/components/ResourceManagement';

export function ReposManagement() {
  return (
    <ResourceManagement
      title="Repos Management"
      path="/repos"
      resourceName="repo"
      queryKey={(page) => ['repos', 'page', page, {includeStats: true}]}
      queryFn={(page) => () => getRepos(page, {includeStats: true})}
      columnBuilders={[
        ["Name", (repo: Repo) => repo.name],
        ["Creation date", (repo: Repo) => repo.created_at],
        ["First log date", (repo: Repo) => repo.stats!.first_log_date || "n/a"],
        ["Last log date", (repo: Repo) => repo.stats!.last_log_date || "n/a"],
        ["Log count", (repo: Repo) => repo.stats!.log_count],
        ["Storage size", (repo: Repo) => repo.stats!.storage_size],
      ]}
      resourceCreationComponentBuilder={(opened) => (
        <RepoCreation opened={opened} />
      )}
      resourceEditionComponentBuilder={(resourceId) => (
        <RepoEdition repoId={resourceId} />
      )}
      resourceDeletionComponentBuilder={(resource, opened, onClose) => (
        <RepoDeletion repo={resource} opened={opened} onClose={onClose} />
      )}
    />
  );
}
