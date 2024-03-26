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
