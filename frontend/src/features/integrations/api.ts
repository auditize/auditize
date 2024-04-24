import camelcaseKeys from 'camelcase-keys';
import { axiosInstance } from '@/utils/axios';

export async function createIntegration(
  name: string
): Promise<[string, string]> {
  const response = await axiosInstance.post(
    '/integrations', {
      name
    }
  );
  return [response.data.id, response.data.token];
}

export async function updateIntegration(id: string, update: IntegrationUpdate): Promise<void> {
  await axiosInstance.patch(`/integrations/${id}`, {
    name: update.name
  });
}

export async function getIntegrations(page = 1): Promise<[Integration[], PagePaginationInfo]> {
  const response = await axiosInstance.get('/integrations', {params: {page}});
  return [
    response.data.data.map(camelcaseKeys),
    response.data.pagination
  ];
}

export async function getIntegration(integrationId: string): Promise<Integration> {
  const response = await axiosInstance.get('/integrations/' + integrationId);
  return camelcaseKeys(response.data);
}

export async function deleteIntegration(integrationId: string): Promise<void> {
  await axiosInstance.delete('/integrations/' + integrationId);
}
