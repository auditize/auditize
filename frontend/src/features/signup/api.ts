import camelcaseKeys from 'camelcase-keys';
import { axiosInstance } from '@/utils/axios';

export async function setPassword(token: string, password: string): Promise<void> {
  await axiosInstance.post(`/users/signup/${token}`, {
    password
  });
}

export async function getSignupInfo(token: string): Promise<SignupInfo> {
  const response = await axiosInstance.get('/users/signup/' + token);
  return camelcaseKeys(response.data);
}
