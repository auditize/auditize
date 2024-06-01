import { useDocumentTitle } from "@mantine/hooks";
import { IconUsers } from "@tabler/icons-react";

import { ResourceManagement } from "@/components/ResourceManagement";
import { useAuthenticatedUser } from "@/features/auth";
import { PermissionSummary } from "@/features/permissions";

import { getUsers, User } from "../api";
import { UserDeletion } from "./UserDeletion";
import { UserCreation, UserEdition } from "./UserEditor";

export function UsersManagement() {
  const { currentUser } = useAuthenticatedUser();
  const readOnly = currentUser.permissions.management.users.write === false;
  useDocumentTitle("Users");

  return (
    <ResourceManagement
      title={
        <>
          <IconUsers /> Users
        </>
      }
      name="User"
      path="/users"
      resourceName="user"
      queryKey={(search, page) => ["users", "list", search, page]}
      queryFn={(search, page) => () => getUsers(search, page)}
      columnBuilders={[
        [
          "Name",
          (user: User) => (
            <span>
              {user.firstName} {user.lastName}
            </span>
          ),
        ],
        ["Email", (user: User) => user.email],
        [
          "Permissions",
          (user: User) => <PermissionSummary permissions={user.permissions} />,
        ],
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
