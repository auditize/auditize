import axios from 'axios';

async function timeout(ms: number) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

export async function getLogs(cursor: string | null, limit = 3): Promise<{logs: Log[], nextCursor: string | null}> {
  await timeout(300);  // FIXME: Simulate network latency

  const response = await axios.get('http://localhost:8000/logs', {
    params: {
      limit,
      ...(cursor && { cursor })
    }
  });
  return {logs: response.data.data, nextCursor: response.data.pagination.next_cursor};
}

export async function getPaginatedItems<T>(url: string, filter = {}): Promise<T[]> {
  await timeout(500);  // FIXME: Simulate network latency

  let page = 1;
  let items: T[] = [];

  while (true) {
    const response = await axios.get(url, {params: {page, ...filter}});
    items.push(...response.data.data);
    if (response.data.pagination.page >= response.data.pagination.total_pages)
      break;
    page++;
  }

  return items;
}

export async function getAllLogEventCategories(): Promise<string[]> {
  return getPaginatedItems<string>('http://localhost:8000/logs/event-categories');
}

export async function getAllLogEventNames(category?: string): Promise<string[]> {
  return getPaginatedItems<string>(
    'http://localhost:8000/logs/events', category ? {category} : {}
  );
}
