import { deleteUser } from '../api';
import { ResourceDeletion } from '@/components/ResourceManagement';

export function UserDeletion({user, opened, onClose}: {user: User, opened: boolean, onClose: () => void}) {
  return (
    <ResourceDeletion
      title={"Confirm deletion"}
      message={`Do you confirm the deletion of user ${user.email} ?`}
      opened={opened}
      onDelete={() => deleteUser(user.id)}
      queryKeyForInvalidation={['users']}
      onClose={onClose}
    />
  );
}
