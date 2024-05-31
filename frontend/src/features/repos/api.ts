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
  permissions: {
    readLogs: boolean;
    writeLogs: boolean;
  };
}

export type RepoUpdate = {
  name?: string;
  status?: RepoStatus;
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
  page = 1,
  { includeStats } = { includeStats: false },
): Promise<[Repo[], PagePaginationInfo]> {
  return await reqGetPaginated("/repos", {
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
}): Promise<Repo[]> {
  return await getAllPagePaginatedItems<Repo>("/users/me/repos", {
    has_read_permission: hasReadPermission,
    has_write_permission: hasWritePermission,
  });
}

export async function getRepo(repoId: string): Promise<Repo> {
  return await reqGet("/repos/" + repoId);
}

export async function deleteRepo(repoId: string): Promise<void> {
  await reqDelete("/repos/" + repoId);
}
