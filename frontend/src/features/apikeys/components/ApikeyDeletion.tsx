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
      message={
        <>
          Do you confirm the deletion of API key <b>{apikey.name}</b> ?
        </>
      }
      opened={opened}
      onDelete={() => deleteApikey(apikey.id)}
      queryKeyForInvalidation={["apikeys"]}
      onClose={onClose}
    />
  );
}
