import {
  camelcaseResourceWithPermissions,
  Permissions,
  snakecaseResourceWithPermissions,
} from "@/features/permissions";
import {
  PagePaginationInfo,
  reqDelete,
  reqGet,
  reqGetPaginated,
  reqPatch,
  reqPost,
} from "@/utils/api";

export interface UserCreation {
  firstName: string;
  lastName: string;
  email: string;
  permissions: Permissions;
}

export interface User extends UserCreation {
  id: string;
}

export type UserUpdate = {
  firstName?: string;
  lastName?: string;
  email?: string;
  permissions?: Permissions;
};

export async function createUser(user: UserCreation): Promise<string> {
  const data = await reqPost("/users", snakecaseResourceWithPermissions(user), {
    disableCaseNormalization: true,
  });
  return data.id;
}

export async function updateUser(
  id: string,
  update: UserUpdate,
): Promise<void> {
  await reqPatch(`/users/${id}`, snakecaseResourceWithPermissions(update), {
    disableCaseNormalization: true,
  });
}

export async function getUsers(
  page = 1,
): Promise<[User[], PagePaginationInfo]> {
  const [data, pagination] = await reqGetPaginated(
    "/users",
    { page },
    {
      disableCaseNormalization: true,
    },
  );
  return [
    data.map((item) => camelcaseResourceWithPermissions(item) as User),
    pagination,
  ];
}

export async function getUser(userId: string): Promise<User> {
  const data = await reqGet(
    `/users/${userId}`,
    {},
    {
      disableCaseNormalization: true,
    },
  );
  return camelcaseResourceWithPermissions(data) as User;
}

export async function deleteUser(userId: string): Promise<void> {
  await reqDelete("/users/" + userId);
}
