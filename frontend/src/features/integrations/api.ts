import { axiosInstance } from "@/utils/axios";

import {
  camelcaseResourceWithPermissions,
  snakecaseResourceWithPermissions,
} from "../permissions";

export async function createIntegration(
  integration: Integration,
): Promise<[string, string]> {
  const response = await axiosInstance.post(
    "/integrations",
    snakecaseResourceWithPermissions(integration),
  );
  return [response.data.id, response.data.token];
}

export async function updateIntegration(
  id: string,
  update: IntegrationUpdate,
): Promise<void> {
  await axiosInstance.patch(
    `/integrations/${id}`,
    snakecaseResourceWithPermissions(update),
  );
}

export async function getIntegrations(
  page = 1,
): Promise<[Integration[], PagePaginationInfo]> {
  const response = await axiosInstance.get("/integrations", {
    params: { page },
  });
  return [
    response.data.data.map(camelcaseResourceWithPermissions),
    response.data.pagination,
  ];
}

export async function getIntegration(
  integrationId: string,
): Promise<Integration> {
  const response = await axiosInstance.get("/integrations/" + integrationId);
  return camelcaseResourceWithPermissions(response.data) as Integration;
}

export async function deleteIntegration(integrationId: string): Promise<void> {
  await axiosInstance.delete("/integrations/" + integrationId);
}

export async function regenerateIntegrationToken(
  integrationId: string,
): Promise<string> {
  const response = await axiosInstance.post(
    `/integrations/${integrationId}/token`,
  );
  return response.data.token;
}
