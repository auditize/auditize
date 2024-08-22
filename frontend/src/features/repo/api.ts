import { useQuery } from "@tanstack/react-query";

import {
  getAllPagePaginatedItems,
  PagePaginationInfo,
  reqDelete,
  reqGet,
  reqGetPaginated,
  reqPatch,
  reqPost,
} from "@/utils/api";

export type RepoStatus = "enabled" | "readonly" | "disabled";

export interface RepoCreation {
  name: string;
  status?: RepoStatus;
  logI18nProfileId?: string | null;
  retentionPeriod?: number | null;
}

export interface Repo extends RepoCreation {
  id: string;
  createdAt: string;
  stats?: {
    firstLogDate: string;
    lastLogDate: string;
    logCount: number;
    storageSize: number;
  };
}

export interface UserRepo {
  id: string;
  name: string;
  permissions: {
    read: boolean;
    write: boolean;
    readableEntities: string[];
  };
}

export type RepoUpdate = {
  name?: string;
  status?: RepoStatus;
  logI18nProfileId?: string | null;
  retentionPeriod?: number | null;
};

export async function createRepo(repo: RepoCreation): Promise<string> {
  const resp = await reqPost("/repos", repo);
  return resp.id;
}

export async function updateRepo(
  id: string,
  update: RepoUpdate,
): Promise<void> {
  await reqPatch(`/repos/${id}`, update);
}

export async function getRepos(
  search: string | null = null,
  page = 1,
  { includeStats } = { includeStats: false },
): Promise<[Repo[], PagePaginationInfo]> {
  return await reqGetPaginated("/repos", {
    q: search,
    page,
    include: includeStats ? "stats" : undefined,
  });
}

export async function getAllMyRepos({
  hasReadPermission,
  hasWritePermission,
}: {
  hasReadPermission?: boolean;
  hasWritePermission?: boolean;
}): Promise<UserRepo[]> {
  return await getAllPagePaginatedItems<UserRepo>("/users/me/repos", {
    has_read_permission: hasReadPermission,
    has_write_permission: hasWritePermission,
  });
}

export async function getRepo(repoId: string): Promise<Repo> {
  return await reqGet("/repos/" + repoId);
}

export async function getRepoTranslation(
  repoId: string,
  lang: string,
): Promise<Record<string, Record<string, string>>> {
  return await reqGet(
    `/repos/${repoId}/translations/${lang}`,
    {},
    { raw: true },
  );
}

export async function deleteRepo(repoId: string): Promise<void> {
  await reqDelete("/repos/" + repoId);
}

export function useLogRepoListQuery({
  enabled = true,
}: { enabled?: boolean } = {}) {
  return useQuery({
    queryKey: ["repos", "available-for-logs"],
    queryFn: () => getAllMyRepos({ hasReadPermission: true }),
    enabled,
  });
}
