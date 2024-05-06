import { axiosInstance } from "./axios";

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
      params: { page, ...filter },
    });
    items.push(...response.data.data);
    if (response.data.pagination.page >= response.data.pagination.total_pages)
      break;
    page++;
  }

  return items;
}
