import camelcaseKeys from "camelcase-keys";

import { axiosInstance } from "@/utils/axios";

export async function logIn(email: string, password: string): Promise<void> {
  await axiosInstance.post("/users/login", {
    email,
    password,
  });
}

export async function getCurrentUserInfo(): Promise<CurrentUserInfo> {
  const response = await axiosInstance.get("/users/me");
  return camelcaseKeys(response.data, { deep: true });
}
