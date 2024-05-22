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
  return (
    <ResourceDeletion
      message={
        <>
          Do you confirm the deletion of log repository <b>{repo.name}</b> ?
        </>
      }
      opened={opened}
      onDelete={() => deleteRepo(repo.id)}
      queryKeyForInvalidation={["repos"]}
      onClose={onClose}
    />
  );
}
