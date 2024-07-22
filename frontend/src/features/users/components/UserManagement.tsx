import { useDocumentTitle } from "@mantine/hooks";
import { IconUsers } from "@tabler/icons-react";
import { useTranslation } from "react-i18next";

import { ResourceManagement } from "@/components/ResourceManagement";
import { useAuthenticatedUser } from "@/features/auth";
import { PermissionSummary } from "@/features/permissions";

import { getUsers, User } from "../api";
import { UserDeletion } from "./UserDeletion";
import { UserCreation, UserEdition } from "./UserEditor";

export function UsersManagement() {
  const { currentUser } = useAuthenticatedUser();
  const { t } = useTranslation();
  const readOnly = currentUser.permissions.management.users.write === false;
  useDocumentTitle(t("user.list.title"));

  return (
    <ResourceManagement
      title={
        <>
          <IconUsers /> {t("user.list.title")}
        </>
      }
      name={t("user.user")}
      path="/users"
      resourceName="user"
      queryKey={(search, page) => ["users", "list", search, page]}
      queryFn={(search, page) => () => getUsers(search, page)}
      columnBuilders={[
        [
          t("user.list.column.name"),
          (user: User) => (
            <span>
              {user.firstName} {user.lastName}
            </span>
          ),
        ],
        [t("user.list.column.email"), (user: User) => user.email],
        [
          t("user.list.column.permissions"),
          (user: User) => <PermissionSummary permissions={user.permissions} />,
        ],
      ]}
      resourceCreationComponentBuilder={
        readOnly
          ? undefined
          : (opened, onClose) => (
              <UserCreation opened={opened} onClose={onClose} />
            )
      }
      resourceEditionComponentBuilder={(resourceId, onClose) => (
        <UserEdition
          userId={resourceId}
          onClose={onClose}
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
