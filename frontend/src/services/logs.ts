import axios from 'axios';

export class LogService {
  private nextCursor: string | null = null;

  private async _getLogs(cursor: string | null): Promise<Log[]> {
    const response = await axios.get('http://localhost:8000/logs?limit=3', {
      params: {
        ...(cursor && { cursor })
      }
    });

    this.nextCursor = response.data.pagination.next_cursor;

    return response.data.data;
  }

  async getLogs(): Promise<Log[]> {
    return await this._getLogs(null);
  }

  async getNextLogs(): Promise<Log[]> {
    return await this._getLogs(this.nextCursor);
  }

  hasMoreLogs(): boolean {
    return this.nextCursor !== null;
  }
}
