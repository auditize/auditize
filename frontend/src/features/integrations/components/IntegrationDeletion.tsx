import { deleteIntegration } from '../api';
import { ResourceDeletion } from '@/components/ResourceManagement';

export function IntegrationDeletion({integration, opened, onClose}: {integration: Integration, opened: boolean, onClose: () => void}) {
  return (
    <ResourceDeletion
      title={"Confirm deletion"}
      message={`Do you confirm the deletion of integration ${integration.name} ?`}
      opened={opened}
      onDelete={() => deleteIntegration(integration.id)}
      queryKeyForInvalidation={['integrations']}
      onClose={onClose}
    />
  );
}
