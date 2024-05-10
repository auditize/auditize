import { ResourceDeletion } from "@/components/ResourceManagement";

import { Apikey, deleteApikey } from "../api";

export function ApikeyDeletion({
  apikey,
  opened,
  onClose,
}: {
  apikey: Apikey;
  opened: boolean;
  onClose: () => void;
}) {
  return (
    <ResourceDeletion
      title={"Confirm deletion"}
      message={`Do you confirm the deletion of apikey ${apikey.name} ?`}
      opened={opened}
      onDelete={() => deleteApikey(apikey.id)}
      queryKeyForInvalidation={["apikeys"]}
      onClose={onClose}
    />
  );
}
