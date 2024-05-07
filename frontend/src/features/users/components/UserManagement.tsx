import { ResourceManagement } from "@/components/ResourceManagement";
import { useAuthenticatedUser } from "@/features/auth";

import { getUsers } from "../api";
import { UserDeletion } from "./UserDeletion";
import { UserCreation, UserEdition } from "./UserEditor";

export function UsersManagement() {
  const { currentUser } = useAuthenticatedUser();
  const readOnly = currentUser.permissions.management.users.write === false;

  return (
    <ResourceManagement
      title="Users Management"
      path="/users"
      resourceName="user"
      queryKey={(page) => ["users", "page", page]}
      queryFn={(page) => () => getUsers(page)}
      columnBuilders={[
        ["Firstname", (user: User) => user.firstName],
        ["Lastname", (user: User) => user.lastName],
        ["Email", (user: User) => user.email],
      ]}
      resourceCreationComponentBuilder={
        readOnly ? undefined : (opened) => <UserCreation opened={opened} />
      }
      resourceEditionComponentBuilder={(resourceId) => (
        <UserEdition
          userId={resourceId}
          readOnly={readOnly || resourceId === currentUser.id}
        />
      )}
      resourceDeletionComponentBuilder={(resource, opened, onClose) =>
        readOnly || currentUser.id === resource.id ? undefined : (
          <UserDeletion user={resource} opened={opened} onClose={onClose} />
        )
      }
    />
  );
}
