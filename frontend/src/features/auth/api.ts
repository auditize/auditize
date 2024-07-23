import { ApplicablePermissions } from "@/features/permissions";
import { reqGet, reqPost } from "@/utils/api";

export type CurrentUserInfo = {
  id: string;
  firstName: string;
  lastName: string;
  email: string;
  lang: string;
  permissions: ApplicablePermissions;
};

export async function logIn(
  email: string,
  password: string,
): Promise<CurrentUserInfo> {
  return await reqPost("/auth/user/login", {
    email,
    password,
  });
}

export async function logOut(): Promise<void> {
  await reqPost("/auth/user/logout", {});
}

export async function getCurrentUserInfo(): Promise<CurrentUserInfo> {
  return reqGet("/users/me");
}
