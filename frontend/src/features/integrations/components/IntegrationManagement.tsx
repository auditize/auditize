import { IntegrationCreation, IntegrationEdition } from './IntegrationEditor';
import { IntegrationDeletion } from './IntegrationDeletion';
import { getIntegrations } from '../api';
import { ResourceManagement } from '@/components/ResourceManagement';

export function IntegrationsManagement() {
  return (
    <ResourceManagement
      title="Integration Management"
      path="/integrations"
      resourceName="integration"
      queryKey={(page) => ['integrations', 'page', page]}
      queryFn={(page) => () => getIntegrations(page)}
      columnBuilders={[
        ["Name", (integration: Integration) => integration.name],
      ]}
      resourceCreationComponentBuilder={(opened) => (
        <IntegrationCreation opened={opened} />
      )}
      resourceEditionComponentBuilder={(resourceId) => (
        <IntegrationEdition integrationId={resourceId} />
      )}
      resourceDeletionComponentBuilder={(resource, opened, onClose) => (
        <IntegrationDeletion integration={resource} opened={opened} onClose={onClose} />
      )}
    />
  );
}
