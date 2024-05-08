import { axiosInstance } from "@/utils/axios";

import {
  camelcaseResourceWithPermissions,
  snakecaseResourceWithPermissions,
} from "../permissions";

export async function createApikey(apikey: Apikey): Promise<[string, string]> {
  const response = await axiosInstance.post(
    "/apikeys",
    snakecaseResourceWithPermissions(apikey),
  );
  return [response.data.id, response.data.token];
}

export async function updateApikey(
  id: string,
  update: ApikeyUpdate,
): Promise<void> {
  await axiosInstance.patch(
    `/apikeys/${id}`,
    snakecaseResourceWithPermissions(update),
  );
}

export async function getApikeys(
  page = 1,
): Promise<[Apikey[], PagePaginationInfo]> {
  const response = await axiosInstance.get("/apikeys", {
    params: { page },
  });
  return [
    response.data.data.map(camelcaseResourceWithPermissions),
    response.data.pagination,
  ];
}

export async function getApikey(apikeyId: string): Promise<Apikey> {
  const response = await axiosInstance.get("/apikeys/" + apikeyId);
  return camelcaseResourceWithPermissions(response.data) as Apikey;
}

export async function deleteApikey(apikeyId: string): Promise<void> {
  await axiosInstance.delete("/apikeys/" + apikeyId);
}

export async function regenerateApikeyToken(apikeyId: string): Promise<string> {
  const response = await axiosInstance.post(`/apikeys/${apikeyId}/token`);
  return response.data.token;
}
