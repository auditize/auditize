import { useQuery } from "@tanstack/react-query";
import React from "react";
import { addQueryParamToLocation } from "@/utils/router";
import { Table, Anchor, Divider, Pagination, Button } from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import { useLocation, Link, useSearchParams, useNavigate } from "react-router-dom";

function ResourceTableRow(
  {
    resourceName, resource, rowValueBuilders, resourceDeletionComponentBuilder,
  }: {
    resourceName: string;
    resource: any;
    rowValueBuilders: ((resource: any) => React.ReactNode)[];
    resourceDeletionComponentBuilder: (
      resource: any, opened: boolean, onClose: () => void
    ) => React.ReactNode;
  }) {
  const location = useLocation();
  const resourceLink = addQueryParamToLocation(location, resourceName, resource.id);
  const [deletionModalOpened, { open: openDeletionModal, close: closeDeletionModal }] = useDisclosure();

  return (
    <Table.Tr>
      <Table.Td>
        <Anchor component={Link} to={resourceLink}>
          {resource.id}
        </Anchor>
      </Table.Td>
      {rowValueBuilders.map(
        (builder, i) => (
          <Table.Td key={i}>{builder(resource)}</Table.Td>
        )
      )}
      <Table.Td>
        <Anchor component={Link} to={resourceLink}>
          Edit
        </Anchor>
        <Divider size="sm" orientation="vertical" />
        <Anchor onClick={() => openDeletionModal()}>
          Delete
        </Anchor>
        {resourceDeletionComponentBuilder(resource, deletionModalOpened, closeDeletionModal)}
      </Table.Td>
    </Table.Tr>
  );
}

export function ResourceManagement(
  {
    title,
    path,
    resourceName,
    queryKey,
    queryFn,
    columnBuilders,
    resourceCreationComponentBuilder,
    resourceEditionComponentBuilder,
    resourceDeletionComponentBuilder,
  }: {
    title: string;
    path: string;
    resourceName: string;
    queryKey: (page: number) => any[];
    queryFn: (page: number) => () => Promise<any>;
    columnBuilders: [string, (resource: any) => React.ReactNode][];
    resourceCreationComponentBuilder: (
      opened: boolean
    ) => React.ReactNode;
    resourceEditionComponentBuilder: (
      resourceId: string | null
    ) => React.ReactNode;
    resourceDeletionComponentBuilder: (
      resource: any, opened: boolean, onClose: () => void
    ) => React.ReactNode;
  }
) {
  const [params] = useSearchParams();
  const location = useLocation();
  const navigate = useNavigate();
  const newResource = params.has('new');
  const resourceId = params.get(resourceName);
  const page = params.has('page') ? parseInt(params.get('page') || "") : 1;
  const { isPending, data, error } = useQuery({
    queryKey: queryKey(page),
    queryFn: queryFn(page)
  });

  if (isPending || !data) {
    return <div>Loading...</div>;
  }

  const [resources, pagination] = data;

  const rows = resources.map((resource: any) => (
    <ResourceTableRow
      key={resource.id}
      resourceName={resourceName}
      resource={resource}
      rowValueBuilders={columnBuilders.map(([_, valueBuilder]) => valueBuilder)}
      resourceDeletionComponentBuilder={resourceDeletionComponentBuilder} />
  ));

  return (
    <div>
      <h1>{title}</h1>
      <Table>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>ID</Table.Th>
            {
              columnBuilders.map(([name, _], i) => (
                <Table.Th key={i}>{name}</Table.Th>
              ))
            }
            <Table.Th>Actions</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {rows}
        </Table.Tbody>
      </Table>
      <Pagination
        total={pagination.total_pages} value={pagination.page}
        onChange={(value) => {
          navigate(addQueryParamToLocation(location, 'page', value.toString()));
        } } />
      <Link to={addQueryParamToLocation(location, "new")}><Button>Create</Button></Link>
      {
        resourceCreationComponentBuilder(newResource)
      }
      {
        resourceEditionComponentBuilder(resourceId)
      }
    </div>
  );
}
