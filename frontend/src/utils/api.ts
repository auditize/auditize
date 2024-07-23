import camelcaseKeys from "camelcase-keys";
import snakecaseKeys from "snakecase-keys";

import { axiosInstance } from "./axios";

export type PagePaginationInfo = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
};

export async function timeout(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export async function getAllPagePaginatedItems<T>(
  path: string,
  filter = {},
): Promise<T[]> {
  let page = 1;
  const allItems: T[] = [];

  while (true) {
    const response = await axiosInstance.get(path, {
      params: snakecaseKeys({ page, ...filter }),
    });
    const { items, pagination } = response.data;
    allItems.push(...camelcaseKeys(items, { deep: true }));
    if (pagination.page >= pagination.total_pages) {
      break;
    }
    page++;
  }

  return allItems;
}

export async function reqPost(
  path: string,
  data: any,
  { disableBodySnakecase }: { disableBodySnakecase?: boolean } = {},
): Promise<any> {
  data = disableBodySnakecase ? data : snakecaseKeys(data, { deep: true });
  const response = await axiosInstance.post(path, data);
  return camelcaseKeys(response.data, { deep: true });
}

export async function reqPatch(
  path: string,
  data: any,
  { disableBodySnakecase }: { disableBodySnakecase?: boolean } = {},
): Promise<any> {
  data = disableBodySnakecase ? data : snakecaseKeys(data, { deep: true });
  const response = await axiosInstance.patch(path, data);
  return camelcaseKeys(response.data, { deep: true });
}

export async function reqDelete(path: string): Promise<void> {
  await axiosInstance.delete(path);
}

export async function reqGet(
  path: string,
  params = {},
  {
    disableParamsSnakecase,
    disableResponseCamelcase,
  }: {
    disableParamsSnakecase?: boolean;
    disableResponseCamelcase?: boolean;
  } = {},
): Promise<any> {
  const response = await axiosInstance.get(path, {
    params: disableParamsSnakecase ? params : snakecaseKeys(params),
  });
  return disableResponseCamelcase
    ? response.data
    : camelcaseKeys(response.data, { deep: true });
}

export async function reqGetPaginated(
  path: string,
  params = {},
  {
    disableResponseCamelcase,
  }: {
    disableResponseCamelcase?: boolean;
  } = {},
): Promise<[any[], PagePaginationInfo]> {
  const response = await axiosInstance.get(path, {
    params: snakecaseKeys(params, { deep: true }),
  });
  return [
    disableResponseCamelcase
      ? response.data.items
      : camelcaseKeys(response.data.items, { deep: true }),
    response.data.pagination,
  ];
}
