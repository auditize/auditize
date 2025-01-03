import { CurrentUserInfo } from "@/features/auth/api";
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
  lang: string;
  permissions: Permissions;
}

export interface User extends UserCreation {
  id: string;
  authenticatedAt: string | null;
}

export type UserUpdate = {
  firstName?: string;
  lastName?: string;
  email?: string;
  lang?: string;
  permissions?: Permissions;
};

export type UserMeUpdate = {
  lang?: string;
  password?: string;
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
  search: string | null = null,
  page = 1,
): Promise<[User[], PagePaginationInfo]> {
  return await reqGetPaginated("/users", { q: search, page });
}

export async function getUser(userId: string): Promise<User> {
  return await reqGet(`/users/${userId}`);
}

export async function deleteUser(userId: string): Promise<void> {
  await reqDelete("/users/" + userId);
}

export async function updateUserMe(
  update: UserMeUpdate,
): Promise<CurrentUserInfo> {
  return await reqPatch(`/users/me`, update);
}
