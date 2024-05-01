import { axiosInstance } from '@/utils/axios';
import camelcaseKeys from 'camelcase-keys';

export async function logIn(email: string, password: string): Promise<void> {
  await axiosInstance.post('/users/login', {
    email,
    password
  });
}

export async function getLoggedInUser(): Promise<LoggedInUserInfo> {
  const response = await axiosInstance.get('/users/me');
  return camelcaseKeys(response.data);
}