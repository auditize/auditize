import camelcaseKeys from "camelcase-keys";
import snakecaseKeys from "snakecase-keys";

import { axiosInstance } from "./axios";

export type PagePaginationInfo = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
};

export type ReqOptions = {
  disableCaseNormalization: boolean;
};

export async function timeout(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export async function getAllPagePaginatedItems<T>(
  path: string,
  filter = {},
  options: ReqOptions = {
    disableCaseNormalization: true,
  },
): Promise<T[]> {
  let page = 1;
  let items: T[] = [];

  while (true) {
    const response = await axiosInstance.get(path, {
      params: snakecaseKeys({ page, ...filter }),
    });
    items.push(
      ...(options.disableCaseNormalization
        ? response.data.data
        : camelcaseKeys(response.data.data, { deep: true })),
    );
    if (response.data.pagination.page >= response.data.pagination.total_pages)
      break;
    page++;
  }

  return items;
}

export async function reqPost(
  path: string,
  data: any,
  options: ReqOptions = {
    disableCaseNormalization: false,
  },
): Promise<any> {
  if (!options.disableCaseNormalization) {
    data = snakecaseKeys(data, { deep: true });
  }
  const response = await axiosInstance.post(path, data);
  return options.disableCaseNormalization
    ? response.data
    : camelcaseKeys(response.data, { deep: true });
}

export async function reqPatch(
  path: string,
  data: any,
  options: ReqOptions = {
    disableCaseNormalization: false,
  },
): Promise<any> {
  if (!options.disableCaseNormalization) {
    data = snakecaseKeys(data, { deep: true });
  }
  const response = await axiosInstance.patch(path, data);
  return options.disableCaseNormalization
    ? response.data
    : camelcaseKeys(response.data, { deep: true });
}

export async function reqDelete(path: string): Promise<void> {
  await axiosInstance.delete(path);
}

export async function reqGet(
  path: string,
  params = {},
  options: ReqOptions = {
    disableCaseNormalization: false,
  },
): Promise<any> {
  const response = await axiosInstance.get(path, {
    params: snakecaseKeys(params),
  });
  return options.disableCaseNormalization
    ? response.data
    : camelcaseKeys(response.data, { deep: true });
}

export async function reqGetPaginated(
  path: string,
  params = {},
  options: ReqOptions = {
    disableCaseNormalization: false,
  },
): Promise<[any[], PagePaginationInfo]> {
  const response = await axiosInstance.get(path, {
    params: snakecaseKeys(params, { deep: true }),
  });
  return [
    options.disableCaseNormalization
      ? response.data.data
      : camelcaseKeys(response.data.data, { deep: true }),
    response.data.pagination,
  ];
}
