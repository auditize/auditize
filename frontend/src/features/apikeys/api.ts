import { Permissions } from "@/features/permissions";
import {
  PagePaginationInfo,
  reqDelete,
  reqGet,
  reqGetPaginated,
  reqPatch,
  reqPost,
} from "@/utils/api";

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
  const data = await reqPost("/apikeys", apikey);
  return [data.id, data.key];
}

export async function updateApikey(
  id: string,
  update: ApikeyUpdate,
): Promise<void> {
  await reqPatch(`/apikeys/${id}`, update);
}

export async function getApikeys(
  page = 1,
): Promise<[Apikey[], PagePaginationInfo]> {
  return await reqGetPaginated("/apikeys", { page });
}

export async function getApikey(apikeyId: string): Promise<Apikey> {
  return await reqGet(`/apikeys/${apikeyId}`);
}

export async function deleteApikey(apikeyId: string): Promise<void> {
  await reqDelete(`/apikeys/${apikeyId}`);
}

export async function regenerateApikey(apikeyId: string): Promise<string> {
  const data = await reqPost(`/apikeys/${apikeyId}/regenerate`, {});
  return data.key;
}
