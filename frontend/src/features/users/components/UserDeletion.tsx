import { ResourceDeletion } from "@/components/ResourceManagement";

import { deleteUser, User } from "../api";

export function UserDeletion({
  user,
  opened,
  onClose,
}: {
  user: User;
  opened: boolean;
  onClose: () => void;
}) {
  return (
    <ResourceDeletion
      message={
        <>
          Do you confirm the deletion of user{" "}
          <b>
            {user.firstName} {user.lastName}
          </b>
          ?
        </>
      }
      opened={opened}
      onDelete={() => deleteUser(user.id)}
      queryKeyForInvalidation={["users"]}
      onClose={onClose}
    />
  );
}
