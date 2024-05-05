import camelcaseKeys from 'camelcase-keys';
import snakecaseKeys from 'snakecase-keys';
import { axiosInstance } from '@/utils/axios';

export async function createUser(user: User): Promise<string> {
  const response = await axiosInstance.post(
    '/users', snakecaseKeys(user, {deep: true})
  );
  return response.data.id;
}

export async function updateUser(id: string, update: UserUpdate): Promise<void> {
  await axiosInstance.patch(`/users/${id}`, snakecaseKeys(update, {deep: true}));
}

export async function getUsers(page = 1): Promise<[User[], PagePaginationInfo]> {
  const response = await axiosInstance.get('/users', {params: {page}});
  return [
    response.data.data.map((item: User) => camelcaseKeys(item, {deep: true})),
    response.data.pagination
  ];
}

export async function getUser(userId: string): Promise<User> {
  const response = await axiosInstance.get('/users/' + userId);
  return camelcaseKeys(response.data, {deep: true});
}

export async function deleteUser(userId: string): Promise<void> {
  await axiosInstance.delete('/users/' + userId);
}
