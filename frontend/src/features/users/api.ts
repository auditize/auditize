import { Permissions } from "@/features/permissions";
import {
  PagePaginationInfo,
  reqDelete,
  reqGet,
  reqGetPaginated,
  reqPatch,
  reqPost,
} from "@/utils/api";

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
  const data = await reqPost("/users", user);
  return data.id;
}

export async function updateUser(
  id: string,
  update: UserUpdate,
): Promise<void> {
  await reqPatch(`/users/${id}`, update);
}

export async function getUsers(
  page = 1,
): Promise<[User[], PagePaginationInfo]> {
  return await reqGetPaginated("/users", { page });
}

export async function getUser(userId: string): Promise<User> {
  return await reqGet(`/users/${userId}`);
}

export async function deleteUser(userId: string): Promise<void> {
  await reqDelete("/users/" + userId);
}
