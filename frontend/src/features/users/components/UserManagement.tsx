import { UserCreation, UserEdition } from './UserEditor';
import { UserDeletion } from './UserDeletion';
import { getUsers } from '../api';
import { ResourceManagement } from '@/components/ResourceManagement';
import { useAuthenticatedUser } from '@/features/auth';

export function UsersManagement() {
  const {currentUser} = useAuthenticatedUser();

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
        (currentUser.id !== resource.id) &&
          <UserDeletion user={resource} opened={opened} onClose={onClose} />
      )}
    />
  );
}
