import { deleteRepo } from '../api';
import { ResourceDeletion } from '@/components/ResourceManagement';

export function RepoDeletion({repo, opened, onClose}: {repo: Repo, opened: boolean, onClose: () => void}) {
  return (
    <ResourceDeletion
      title={"Confirm deletion"}
      message={`Do you confirm the deletion of log repository ${repo.name} ?`}
      opened={opened}
      onDelete={() => deleteRepo(repo.id)}
      queryKeyForInvalidation={['repos']}
      onClose={onClose}
    />
  );
}
