import { Trans } from "react-i18next";

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
        <Trans i18nKey="repo.delete.confirm" values={{ name: apikey.name }}>
          Do you confirm the deletion of API key <b>{apikey.name}</b> ?
        </Trans>
      }
      opened={opened}
      onDelete={() => deleteApikey(apikey.id)}
      queryKeyForInvalidation={["apikeys"]}
      onClose={onClose}
    />
  );
}
