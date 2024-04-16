import { getAllPagePaginatedItems } from '@/utils/api';
import axios from 'axios';

export async function createRepo({name}: {name: string}): Promise<string> {
  const response = await axios.post('http://localhost:8000/repos', {name});
  return response.data.id;
}

export async function updateRepo(id: string, update: RepoUpdate): Promise<void> {
  await axios.patch(`http://localhost:8000/repos/${id}`, update);
}

export async function getRepos(
  page = 1,
  {includeStats} = {includeStats: false}):
  Promise<[Repo[], PagePaginationInfo]> {
  const response = await axios.get(
    'http://localhost:8000/repos',
    {params: {page, ...(includeStats && {include: 'stats'})}}
  );
  return [response.data.data, response.data.pagination];
}

export async function getAllRepos(): Promise<Repo[]> {
  return await getAllPagePaginatedItems<Repo>('http://localhost:8000/repos');
}

export async function getRepo(repoId: string): Promise<Repo> {
  const response = await axios.get('http://localhost:8000/repos/' + repoId);
  return response.data;
}

export async function deleteRepo(repoId: string): Promise<void> {
  await axios.delete('http://localhost:8000/repos/' + repoId);
}
