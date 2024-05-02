import camelcaseKeys from 'camelcase-keys';
import snakecaseKeys from 'snakecase-keys';
import { axiosInstance } from '@/utils/axios';

export async function createIntegration(integration: Integration): Promise<[string, string]> {
  const response = await axiosInstance.post(
    '/integrations', snakecaseKeys(integration, {deep: true})
  );
  return [response.data.id, response.data.token];
}

export async function updateIntegration(id: string, update: IntegrationUpdate): Promise<void> {
  await axiosInstance.patch(`/integrations/${id}`, snakecaseKeys(update, {deep: true}));
}

export async function getIntegrations(page = 1): Promise<[Integration[], PagePaginationInfo]> {
  const response = await axiosInstance.get('/integrations', {params: {page}});
  return [
    response.data.data.map((item: Integration) => camelcaseKeys(item, {deep: true})),
    response.data.pagination
  ];
}

export async function getIntegration(integrationId: string): Promise<Integration> {
  const response = await axiosInstance.get('/integrations/' + integrationId);
  return camelcaseKeys(response.data, {deep: true});
}

export async function deleteIntegration(integrationId: string): Promise<void> {
  await axiosInstance.delete('/integrations/' + integrationId);
}

export async function regenerateIntegrationToken(integrationId: string): Promise<string> {
  const response = await axiosInstance.post(`/integrations/${integrationId}/token`);
  return response.data.token;
}
