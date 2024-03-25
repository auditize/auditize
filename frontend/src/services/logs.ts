import axios from 'axios';

export async function getLogs(cursor: string | null, limit = 3): Promise<{logs: Log[], nextCursor: string | null}> {
  const response = await axios.get('http://localhost:8000/logs', {
    params: {
      limit,
      ...(cursor && { cursor })
    }
  });
  return {logs: response.data.data, nextCursor: response.data.pagination.next_cursor};
}
