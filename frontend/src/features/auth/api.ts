import camelcaseKeys from "camelcase-keys";

import { ApplicablePermissions } from "@/features/permissions";
import { axiosInstance } from "@/utils/axios";

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
  const response = await axiosInstance.post("/auth/user/login", {
    email,
    password,
  });
  return camelcaseKeys(response.data, { deep: true });
}

export async function logOut(): Promise<void> {
  await axiosInstance.post("/auth/user/logout");
}

export async function getCurrentUserInfo(): Promise<CurrentUserInfo> {
  const response = await axiosInstance.get("/users/me");
  return camelcaseKeys(response.data, { deep: true });
}
