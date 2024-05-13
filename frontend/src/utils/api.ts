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
  let items: T[] = [];

  while (true) {
    const response = await axiosInstance.get(path, {
      params: snakecaseKeys({ page, ...filter }),
    });
    const { data, pagination } = response.data;
    items.push(...camelcaseKeys(data, { deep: true }));
    if (pagination.page >= pagination.total_pages) break;
    page++;
  }

  return items;
}

export async function reqPost(path: string, data: any): Promise<any> {
  data = snakecaseKeys(data, { deep: true });
  const response = await axiosInstance.post(path, data);
  return camelcaseKeys(response.data, { deep: true });
}

export async function reqPatch(path: string, data: any): Promise<any> {
  data = snakecaseKeys(data, { deep: true });
  const response = await axiosInstance.patch(path, data);
  return camelcaseKeys(response.data, { deep: true });
}

export async function reqDelete(path: string): Promise<void> {
  await axiosInstance.delete(path);
}

export async function reqGet(path: string, params = {}): Promise<any> {
  const response = await axiosInstance.get(path, {
    params: snakecaseKeys(params),
  });
  return camelcaseKeys(response.data, { deep: true });
}

export async function reqGetPaginated(
  path: string,
  params = {},
): Promise<[any[], PagePaginationInfo]> {
  const response = await axiosInstance.get(path, {
    params: snakecaseKeys(params, { deep: true }),
  });
  return [
    camelcaseKeys(response.data.data, { deep: true }),
    response.data.pagination,
  ];
}
