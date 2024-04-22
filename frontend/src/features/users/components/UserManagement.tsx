import { UserCreation, UserEdition } from './UserEditor';
import { UserDeletion } from './UserDeletion';
import { getUsers } from '../api';
import { ResourceManagement } from '@/components/ResourceManagement';

export function UsersManagement() {
  return (
    <ResourceManagement
      title="Users Management"
      path="/users"
      resourceName="user"
      queryKey={(page) => ['users', 'page', page]}
      queryFn={(page) => () => getUsers(page)}
      columnBuilders={[
        ["Firstname", (user: User) => user.firstName],
        ["Lastname", (user: User) => user.lastName],
        ["Email", (user: User) => user.email],
      ]}
      resourceCreationComponentBuilder={(opened) => (
        <UserCreation opened={opened} />
      )}
      resourceEditionComponentBuilder={(resourceId) => (
        <UserEdition userId={resourceId} />
      )}
      resourceDeletionComponentBuilder={(resource, opened, onClose) => (
        <UserDeletion user={resource} opened={opened} onClose={onClose} />
      )}
    />
  );
}
