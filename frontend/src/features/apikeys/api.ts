import { Permissions } from "@/features/permissions";
import {
  PagePaginationInfo,
  reqDelete,
  reqGet,
  reqGetPaginated,
  reqPatch,
  reqPost,
} from "@/utils/api";

import {
  camelcaseResourceWithPermissions,
  snakecaseResourceWithPermissions,
} from "../permissions";

export interface ApikeyCreation {
  name: string;
  permissions: Permissions;
}

export interface Apikey extends ApikeyCreation {
  id: string;
}

export type ApikeyUpdate = {
  name?: string;
  permissions?: Permissions;
};

export async function createApikey(
  apikey: ApikeyCreation,
): Promise<[string, string]> {
  const data = await reqPost(
    "/apikeys",
    snakecaseResourceWithPermissions(apikey),
    { disableCaseNormalization: true },
  );
  return [data.id, data.key];
}

export async function updateApikey(
  id: string,
  update: ApikeyUpdate,
): Promise<void> {
  await reqPatch(`/apikeys/${id}`, snakecaseResourceWithPermissions(update), {
    disableCaseNormalization: true,
  });
}

export async function getApikeys(
  page = 1,
): Promise<[Apikey[], PagePaginationInfo]> {
  const [data, pagination] = await reqGetPaginated(
    "/apikeys",
    { page },
    { disableCaseNormalization: true },
  );
  return [data.map(camelcaseResourceWithPermissions) as Apikey[], pagination];
}

export async function getApikey(apikeyId: string): Promise<Apikey> {
  const data = await reqGet(
    `/apikeys/${apikeyId}`,
    {},
    {
      disableCaseNormalization: true,
    },
  );
  return camelcaseResourceWithPermissions(data) as Apikey;
}

export async function deleteApikey(apikeyId: string): Promise<void> {
  await reqDelete(`/apikeys/${apikeyId}`);
}

export async function regenerateApikey(apikeyId: string): Promise<string> {
  const data = await reqPost(
    `/apikeys/${apikeyId}/regenerate`,
    {},
    {
      disableCaseNormalization: true,
    },
  );
  return data.key;
}
