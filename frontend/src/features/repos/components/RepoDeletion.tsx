import { Trans, useTranslation } from "react-i18next";

import { ResourceDeletion } from "@/components/ResourceManagement";

import { deleteRepo, Repo } from "../api";

export function RepoDeletion({
  repo,
  opened,
  onClose,
}: {
  repo: Repo;
  opened: boolean;
  onClose: () => void;
}) {
  const { t } = useTranslation();
  return (
    <ResourceDeletion
      message={
        <Trans i18nKey="repo.delete.confirm" values={{ name: repo.name }}>
          Do you confirm the deletion of log repository <b>{repo.name}</b> ?
        </Trans>
      }
      opened={opened}
      onDelete={() => deleteRepo(repo.id)}
      queryKeyForInvalidation={["repos"]}
      onClose={onClose}
    />
  );
}
