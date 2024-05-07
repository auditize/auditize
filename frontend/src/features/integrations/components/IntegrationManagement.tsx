import { ResourceManagement } from "@/components/ResourceManagement";
import { useAuthenticatedUser } from "@/features/auth";

import { getIntegrations } from "../api";
import { IntegrationDeletion } from "./IntegrationDeletion";
import { IntegrationCreation, IntegrationEdition } from "./IntegrationEditor";

export function IntegrationsManagement() {
  const { currentUser } = useAuthenticatedUser();
  const readOnly =
    currentUser.permissions.management.integrations.write === false;

  return (
    <ResourceManagement
      title="Integration Management"
      path="/integrations"
      resourceName="integration"
      queryKey={(page) => ["integrations", "page", page]}
      queryFn={(page) => () => getIntegrations(page)}
      columnBuilders={[
        ["Name", (integration: Integration) => integration.name],
      ]}
      resourceCreationComponentBuilder={
        readOnly
          ? undefined
          : (opened) => <IntegrationCreation opened={opened} />
      }
      resourceEditionComponentBuilder={(resourceId) => (
        <IntegrationEdition integrationId={resourceId} readOnly={readOnly} />
      )}
      resourceDeletionComponentBuilder={(resource, opened, onClose) =>
        readOnly ? undefined : (
          <IntegrationDeletion
            integration={resource}
            opened={opened}
            onClose={onClose}
          />
        )
      }
    />
  );
}
