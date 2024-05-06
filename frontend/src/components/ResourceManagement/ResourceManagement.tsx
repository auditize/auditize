import { Anchor, Button, Divider, Pagination, Table } from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import { useQuery } from "@tanstack/react-query";
import React, { createElement } from "react";
import {
  Link,
  useLocation,
  useNavigate,
  useSearchParams,
} from "react-router-dom";

import { addQueryParamToLocation } from "@/utils/router";

type ResourceCreationComponentBuilder = (opened: boolean) => React.ReactNode;
type ResourceEditionComponentBuilder = (
  resourceId: string | null,
) => React.ReactNode;
type ResourceDeletionComponentBuilder = (
  resource: any,
  opened: boolean,
  onClose: () => void,
) => React.ReactNode;

function ResourceDeletionAction({
  resource,
  componentBuilder,
}: {
  resource: any;
  componentBuilder: ResourceDeletionComponentBuilder;
}) {
  const [opened, { open, close }] = useDisclosure();
  const component = componentBuilder(resource, opened, close);

  if (!component) return null;

  return (
    <>
      <Anchor onClick={() => open()}>Delete</Anchor>
      {component}
    </>
  );
}

function ResourceTableRow({
  resourceName,
  resource,
  rowValueBuilders,
  resourceDeletionComponentBuilder,
}: {
  resourceName: string;
  resource: any;
  rowValueBuilders: ((resource: any) => React.ReactNode)[];
  resourceDeletionComponentBuilder: ResourceDeletionComponentBuilder;
}) {
  const location = useLocation();
  const resourceLink = addQueryParamToLocation(
    location,
    resourceName,
    resource.id,
  );

  const resourceDeletionAction = createElement(ResourceDeletionAction, {
    resource: resource,
    componentBuilder: resourceDeletionComponentBuilder,
  });

  return (
    <Table.Tr>
      <Table.Td>
        <Anchor component={Link} to={resourceLink}>
          {resource.id}
        </Anchor>
      </Table.Td>
      {rowValueBuilders.map((builder, i) => (
        <Table.Td key={i}>{builder(resource)}</Table.Td>
      ))}
      <Table.Td>
        <Anchor component={Link} to={resourceLink}>
          Edit
        </Anchor>
        {resourceDeletionAction && (
          <>
            <Divider size="sm" orientation="vertical" />
            {resourceDeletionAction}
          </>
        )}
      </Table.Td>
    </Table.Tr>
  );
}

export function ResourceManagement({
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
  resourceCreationComponentBuilder?: ResourceCreationComponentBuilder;
  resourceEditionComponentBuilder: ResourceEditionComponentBuilder;
  resourceDeletionComponentBuilder: ResourceDeletionComponentBuilder;
}) {
  const [params] = useSearchParams();
  const location = useLocation();
  const navigate = useNavigate();
  const newResource = params.has("new");
  const resourceId = params.get(resourceName);
  const page = params.has("page") ? parseInt(params.get("page") || "") : 1;
  const { isPending, data, error } = useQuery({
    queryKey: queryKey(page),
    queryFn: queryFn(page),
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
      resourceDeletionComponentBuilder={resourceDeletionComponentBuilder}
    />
  ));

  return (
    <div>
      <h1>{title}</h1>
      <Table>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>ID</Table.Th>
            {columnBuilders.map(([name, _], i) => (
              <Table.Th key={i}>{name}</Table.Th>
            ))}
            <Table.Th>Actions</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>{rows}</Table.Tbody>
      </Table>
      <Pagination
        total={pagination.total_pages}
        value={pagination.page}
        onChange={(value) => {
          navigate(addQueryParamToLocation(location, "page", value.toString()));
        }}
      />
      {resourceCreationComponentBuilder && (
        <Link to={addQueryParamToLocation(location, "new")}>
          <Button>Create</Button>
        </Link>
      )}
      {resourceCreationComponentBuilder &&
        resourceCreationComponentBuilder(newResource)}
      {resourceEditionComponentBuilder(resourceId)}
    </div>
  );
}
