import {
  getAllPagePaginatedItems,
  PagePaginationInfo,
  reqDelete,
  reqGet,
  reqGetPaginated,
  reqPatch,
  reqPost,
} from "@/utils/api";

export interface LogI18nProfileCreation {
  name: string;
  translations: Record<string, object>;
}

export interface LogI18nProfile extends LogI18nProfileCreation {
  id: string;
  createdAt: string;
  updatedAt: string;
}

export type LogI18nProfileUpdate = {
  name?: string;
  translations?: Record<string, object | null>;
};

export async function createLogI18nProfile(
  profile: LogI18nProfileCreation,
): Promise<string> {
  const resp = await reqPost("/log-i18n-profiles", profile);
  return resp.id;
}

export async function updateLogi18nProfile(
  id: string,
  update: LogI18nProfileUpdate,
): Promise<void> {
  await reqPatch(`/log-i18n-profiles/${id}`, update);
}

export async function getLogI18nProfiles(
  search: string | null = null,
  page = 1,
): Promise<[LogI18nProfile[], PagePaginationInfo]> {
  return await reqGetPaginated("/log-i18n-profiles", {
    q: search,
    page,
  });
}

export async function getAllLogI18nProfiles(): Promise<LogI18nProfile[]> {
  return await getAllPagePaginatedItems<LogI18nProfile>("/log-i18n-profiles");
}

export async function getLogI18nProfile(
  profileId: string,
): Promise<LogI18nProfile> {
  return await reqGet("/log-i18n-profiles/" + profileId);
}

export async function deleteLogI18nProfile(profileId: string): Promise<void> {
  await reqDelete("/log-i18n-profiles/" + profileId);
}
