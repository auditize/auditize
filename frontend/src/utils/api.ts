import axios from "axios";

export async function timeout(ms: number) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

export async function getAllPagePaginatedItems<T>(url: string, filter = {}): Promise<T[]> {
  await timeout(500); // FIXME: Simulate network latency

  let page = 1;
  let items: T[] = [];

  while (true) {
    const response = await axios.get(url, { params: { page, ...filter } });
    items.push(...response.data.data);
    if (response.data.pagination.page >= response.data.pagination.total_pages)
      break;
    page++;
  }

  return items;
}

