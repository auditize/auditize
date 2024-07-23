import { reqGet, reqPost } from "@/utils/api";

type SignupInfo = {
  firstName: string;
  lastName: string;
  email: string;
};

export async function setPassword(
  token: string,
  password: string,
): Promise<void> {
  await reqPost(`/users/signup/${token}`, { password });
}

export async function getSignupInfo(token: string): Promise<SignupInfo> {
  return reqGet(`/users/signup/${token}`);
}
