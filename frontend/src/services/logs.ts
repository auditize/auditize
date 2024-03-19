export async function getLogs(): Promise<Log[]> {
  const response = await fetch('http://localhost:8000/logs');
  return (await response.json()).data as Log[];
}