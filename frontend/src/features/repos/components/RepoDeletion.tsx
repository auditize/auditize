import { ResourceDeletion } from "@/components/ResourceManagement";

import { deleteRepo } from "../api";

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
      title={"Confirm deletion"}
      message={`Do you confirm the deletion of log repository ${repo.name} ?`}
      opened={opened}
      onDelete={() => deleteRepo(repo.id)}
      queryKeyForInvalidation={["repos"]}
      onClose={onClose}
    />
  );
}
