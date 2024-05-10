import {
  camelcaseResourceWithPermissions,
  Permissions,
  snakecaseResourceWithPermissions,
} from "@/features/permissions";
import { PagePaginationInfo } from "@/utils/api";
import { axiosInstance } from "@/utils/axios";

export interface UserCreation {
  firstName: string;
  lastName: string;
  email: string;
  permissions: Permissions;
}

export interface User extends UserCreation {
  id: string;
}

export type UserUpdate = {
  firstName?: string;
  lastName?: string;
  email?: string;
  permissions?: Permissions;
};

export async function createUser(user: UserCreation): Promise<string> {
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
