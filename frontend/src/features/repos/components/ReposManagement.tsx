import { Anchor, Button, Table, Divider, Pagination } from '@mantine/core';
import { RepoCreation, RepoEdition } from './RepoEditor';
import { RepoDeletion } from './RepoDeletion';
import { getRepos } from '../api';
import { Link, useSearchParams, useLocation, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { useDisclosure } from '@mantine/hooks';
import { addQueryParamToLocation } from '@/utils/router';

function RepoTableRow({repo}: {repo: Repo}) {
  const location = useLocation();
  const repoLink = addQueryParamToLocation(location, "repo", repo.id);
  const [deletionModalOpened, {open: openDeletionModal, close: closeDeletionModal}] = useDisclosure();

  return (
    <Table.Tr>
      <Table.Td>
        <Anchor component={Link} to={repoLink}>
          {repo.id}
        </Anchor>
      </Table.Td>
      <Table.Td>{repo.name}</Table.Td>
      <Table.Td>{repo.created_at}</Table.Td>
      <Table.Td>{repo.stats!.first_log_date || "n/a"}</Table.Td>
      <Table.Td>{repo.stats!.last_log_date || "n/a"}</Table.Td>
      <Table.Td>{repo.stats!.log_count}</Table.Td>
      <Table.Td>{repo.stats!.storage_size}</Table.Td>
      <Table.Td>
        <Anchor component={Link} to={repoLink}>
          Edit
        </Anchor>
        <Divider size="sm" orientation="vertical" />
        <Anchor onClick={() => openDeletionModal()}>
          Delete
        </Anchor>
        <RepoDeletion repo={repo} opened={deletionModalOpened} onClose={closeDeletionModal}/>
      </Table.Td>
    </Table.Tr>
  );
}

export function ReposManagement() {
  const [params] = useSearchParams();
  const location = useLocation();
  const navigate = useNavigate();
  const newRepo = params.has('new');
  const repoId = params.get('repo');
  const page = params.has('page') ? parseInt(params.get('page') || "") : 1;
  const { isPending, data, error } = useQuery({
    queryKey: ['repos', 'page', page],
    queryFn: () => getRepos(page, {includeStats: true})
  });

  if (isPending || !data) {
    return <div>Loading...</div>;
  }

  const [repos, pagination] = data;

  const rows = repos.map((repo) => <RepoTableRow key={repo.id} repo={repo}/>);

  return (
    <div>
      <h1>Repos Management</h1>
      <Table>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>ID</Table.Th>
            <Table.Th>Name</Table.Th>
            <Table.Th>Creation date</Table.Th>
            <Table.Th>First log date</Table.Th>
            <Table.Th>Last log date</Table.Th>
            <Table.Th>Log count</Table.Th>
            <Table.Th>Storage size</Table.Th>
            <Table.Th>Actions</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {rows}
        </Table.Tbody>
      </Table>
      <Pagination
        total={pagination.total_pages} value={pagination.page}
        onChange={
          (value) => {
            navigate(addQueryParamToLocation(location, 'page', value.toString()));
          }
        }
      />
      <Link to='/repos?new'><Button>Create</Button></Link>
      <RepoCreation opened={newRepo}/>
      <RepoEdition repoId={repoId}/>
    </div>
  );
}