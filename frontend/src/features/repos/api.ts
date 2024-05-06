import { getAllPagePaginatedItems } from "@/utils/api";
import { axiosInstance } from "@/utils/axios";

export async function createRepo({ name }: { name: string }): Promise<string> {
  const response = await axiosInstance.post("/repos", { name });
  return response.data.id;
}

export async function updateRepo(
  id: string,
  update: RepoUpdate,
): Promise<void> {
  await axiosInstance.patch(`/repos/${id}`, update);
}

export async function getRepos(
  page = 1,
  { includeStats } = { includeStats: false },
): Promise<[Repo[], PagePaginationInfo]> {
  const response = await axiosInstance.get("/repos", {
    params: { page, ...(includeStats && { include: "stats" }) },
  });
  return [response.data.data, response.data.pagination];
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
  const response = await axiosInstance.get("/repos/" + repoId);
  return response.data;
}

export async function deleteRepo(repoId: string): Promise<void> {
  await axiosInstance.delete("/repos/" + repoId);
}
