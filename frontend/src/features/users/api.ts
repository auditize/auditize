import { axiosInstance } from "@/utils/axios";

import {
  camelcaseResourceWithPermissions,
  snakecaseResourceWithPermissions,
} from "../permissions";

export async function createUser(user: User): Promise<string> {
  const response = await axiosInstance.post(
    "/users",
    snakecaseResourceWithPermissions(user),
  );
  return response.data.id;
}

export async function updateUser(
  id: string,
  update: UserUpdate,
): Promise<void> {
  await axiosInstance.patch(
    `/users/${id}`,
    snakecaseResourceWithPermissions(update),
  );
}

export async function getUsers(
  page = 1,
): Promise<[User[], PagePaginationInfo]> {
  const response = await axiosInstance.get("/users", { params: { page } });
  return [
    response.data.data.map((item: User) =>
      camelcaseResourceWithPermissions(item),
    ),
    response.data.pagination,
  ];
}

export async function getUser(userId: string): Promise<User> {
  const response = await axiosInstance.get("/users/" + userId);
  return camelcaseResourceWithPermissions(response.data) as User;
}

export async function deleteUser(userId: string): Promise<void> {
  await axiosInstance.delete("/users/" + userId);
}
