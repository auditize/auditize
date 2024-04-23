import camelcaseKeys from 'camelcase-keys';
import { axiosInstance } from '@/utils/axios';

export async function createUser(
  firstName: string, lastName: string, email: string
): Promise<string> {
  const response = await axiosInstance.post(
    '/users', {
      first_name: firstName,
      last_name: lastName,
      email: email
    }
  );
  return response.data.id;
}

export async function updateUser(id: string, update: UserUpdate): Promise<void> {
  await axiosInstance.patch(`/users/${id}`, {
    first_name: update.firstName,
    last_name: update.lastName,
    email: update.email
  });
}

export async function getUsers(page = 1): Promise<[User[], PagePaginationInfo]> {
  const response = await axiosInstance.get('/users', {params: {page}});
  return [
    response.data.data.map(camelcaseKeys),
    response.data.pagination
  ];
}

export async function getUser(userId: string): Promise<User> {
  const response = await axiosInstance.get('/users/' + userId);
  return camelcaseKeys(response.data);
}

export async function deleteUser(userId: string): Promise<void> {
  await axiosInstance.delete('/users/' + userId);
}
