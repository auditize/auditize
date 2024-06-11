import { Trans, useTranslation } from "react-i18next";

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
  const { t } = useTranslation();
  const name = user.firstName + " " + user.lastName;
  return (
    <ResourceDeletion
      message={
        <Trans i18nKey="user.delete.confirm" values={{ name: name }}>
          Do you confirm the deletion of user <b>{name}</b> ?
        </Trans>
      }
      opened={opened}
      onDelete={() => deleteUser(user.id)}
      queryKeyForInvalidation={["users"]}
      onClose={onClose}
    />
  );
}
