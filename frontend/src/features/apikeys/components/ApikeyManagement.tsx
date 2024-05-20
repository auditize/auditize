import { ResourceManagement } from "@/components/ResourceManagement";
import { useAuthenticatedUser } from "@/features/auth";

import { Apikey, getApikeys } from "../api";
import { ApikeyDeletion } from "./ApikeyDeletion";
import { ApikeyCreation, ApikeyEdition } from "./ApikeyEditor";

export function ApikeysManagement() {
  const { currentUser } = useAuthenticatedUser();
  const readOnly = currentUser.permissions.management.apikeys.write === false;

  return (
    <ResourceManagement
      title="API keys"
      path="/apikeys"
      resourceName="apikey"
      queryKey={(page) => ["apikeys", "page", page]}
      queryFn={(page) => () => getApikeys(page)}
      columnBuilders={[["Name", (apikey: Apikey) => apikey.name]]}
      resourceCreationComponentBuilder={
        readOnly ? undefined : (opened) => <ApikeyCreation opened={opened} />
      }
      resourceEditionComponentBuilder={(resourceId) => (
        <ApikeyEdition apikeyId={resourceId} readOnly={readOnly} />
      )}
      resourceDeletionComponentBuilder={(resource, opened, onClose) =>
        readOnly ? undefined : (
          <ApikeyDeletion apikey={resource} opened={opened} onClose={onClose} />
        )
      }
    />
  );
}
