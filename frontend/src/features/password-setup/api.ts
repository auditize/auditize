import { reqGet, reqPost } from "@/utils/api";

type PasswordResetInfo = {
  firstName: string;
  lastName: string;
  email: string;
};

export async function setPassword(
  token: string,
  password: string,
  lang?: string,
): Promise<void> {
  await reqPost(`/users/password-reset/${token}`, { password }, { lang });
}

export async function getPasswordResetInfo(
  token: string,
): Promise<PasswordResetInfo> {
  return reqGet(`/users/password-reset/${token}`);
}
