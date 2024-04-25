import { axiosInstance } from '@/utils/axios';

export async function log_in(email: string, password: string): Promise<void> {
  await axiosInstance.post('/users/login', {
    email,
    password
  });
}
