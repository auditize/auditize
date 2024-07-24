import { axiosInstance } from "./axios";
import {
  camelCaseToSnakeCaseObjectKeys,
  snakeCaseToCamelCaseObjectKeys,
} from "./switchCase";

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
      params: camelCaseToSnakeCaseObjectKeys({ page, ...filter }),
    });
    const { items, pagination } = response.data;
    allItems.push(...snakeCaseToCamelCaseObjectKeys(items));
    if (pagination.page >= pagination.total_pages) {
      break;
    }
    page++;
  }

  return allItems;
}

export async function reqPost(path: string, data: any): Promise<any> {
  const response = await axiosInstance.post(
    path,
    camelCaseToSnakeCaseObjectKeys(data),
  );
  return snakeCaseToCamelCaseObjectKeys(response.data);
}

export async function reqPatch(path: string, data: any): Promise<any> {
  const response = await axiosInstance.patch(
    path,
    camelCaseToSnakeCaseObjectKeys(data),
  );
  return snakeCaseToCamelCaseObjectKeys(response.data);
}

export async function reqDelete(path: string): Promise<void> {
  await axiosInstance.delete(path);
}

export async function reqGet(
  path: string,
  params = {},
  {
    raw = false,
  }: {
    raw?: boolean;
  } = {},
): Promise<any> {
  const response = await axiosInstance.get(path, {
    params: raw ? params : camelCaseToSnakeCaseObjectKeys(params),
  });
  return raw ? response.data : snakeCaseToCamelCaseObjectKeys(response.data);
}

export async function reqGetPaginated(
  path: string,
  params = {},
): Promise<[any[], PagePaginationInfo]> {
  const response = await axiosInstance.get(path, {
    params: camelCaseToSnakeCaseObjectKeys(params),
  });
  return [
    snakeCaseToCamelCaseObjectKeys(response.data.items),
    response.data.pagination,
  ];
}
