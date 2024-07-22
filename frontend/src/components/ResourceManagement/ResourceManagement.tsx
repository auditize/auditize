import {
  Anchor,
  Button,
  CloseButton,
  Divider,
  Group,
  Pagination,
  Skeleton,
  Stack,
  Table,
  TextInput,
} from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import { IconPlus, IconSearch } from "@tabler/icons-react";
import { useQuery } from "@tanstack/react-query";
import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
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
  const { t } = useTranslation();
  const location = useLocation();
  const [opened, { open, close }] = useDisclosure();
  const resourceLink = addQueryParamToLocation(
    location,
    resourceName,
    resource.id,
  );

  const deletionConfirmModal = resourceDeletionComponentBuilder(
    resource,
    opened,
    close,
  );

  return (
    <Table.Tr>
      {rowValueBuilders.map((builder, i) => (
        <Table.Td key={i}>{builder(resource)}</Table.Td>
      ))}
      <Table.Td style={{ textAlign: "right" }}>
        <Group justify="flex-end" gap={"md"}>
          <Anchor component={Link} to={resourceLink}>
            {t("resource.list.edit")}
          </Anchor>
          {deletionConfirmModal && (
            <>
              <Divider orientation="vertical" />
              <Anchor onClick={() => open()}>
                {t("resource.list.delete")}
              </Anchor>
              {deletionConfirmModal}
            </>
          )}
        </Group>
      </Table.Td>
    </Table.Tr>
  );
}

function Search({ name }: { name: string }) {
  const { t } = useTranslation();
  const [params, setParams] = useSearchParams();
  const [search, setSearch] = useState("");
  const handleSearch = () => setParams({ q: search });

  useEffect(() => {
    setSearch(params.get("q") || "");
  }, [params.get("q")]);

  return (
    <Group gap="xs">
      <TextInput
        placeholder={t("resource.list.search")}
        value={search}
        onChange={(event) => setSearch(event.currentTarget.value)}
        onKeyDown={(event) => {
          if (event.key === "Enter") {
            handleSearch();
          }
        }}
        rightSection={
          search ? (
            <CloseButton
              onClick={() => setSearch("")}
              style={{ display: search ? undefined : "none" }}
            />
          ) : (
            <IconSearch />
          )
        }
      />
      <Button onClick={handleSearch} disabled={!search && !params.get("q")}>
        {t("resource.list.search")}
      </Button>
    </Group>
  );
}

export function ResourceManagement({
  title,
  name,
  path,
  resourceName,
  queryKey,
  queryFn,
  columnBuilders,
  resourceCreationComponentBuilder,
  resourceEditionComponentBuilder,
  resourceDeletionComponentBuilder,
}: {
  title: React.ReactNode;
  name: string;
  path?: string;
  resourceName: string;
  queryKey: (search: string | null, page: number) => any[];
  queryFn: (search: string | null, page: number) => () => Promise<any>;
  columnBuilders: [string, (resource: any) => React.ReactNode][];
  resourceCreationComponentBuilder?: ResourceCreationComponentBuilder;
  resourceEditionComponentBuilder: ResourceEditionComponentBuilder;
  resourceDeletionComponentBuilder: ResourceDeletionComponentBuilder;
}) {
  const { t } = useTranslation();
  const [params] = useSearchParams();
  const location = useLocation();
  const navigate = useNavigate();
  const newResource = params.has("new");
  const resourceId = params.get(resourceName);
  const pageParam = params.has("page") ? parseInt(params.get("page") || "") : 1;
  const searchParam = params.get("q");
  const { isPending, data, error } = useQuery({
    queryKey: queryKey(searchParam, pageParam),
    queryFn: queryFn(searchParam, pageParam),
  });

  if (error) {
    return <div>Error: {error.message}</div>;
  }

  let rows;
  let pagination;
  if (isPending) {
    rows = Array.from({ length: 10 }).map((_, rowIndex) => (
      <Table.Tr key={rowIndex} style={{ height: "2rem" }}>
        {Array.from({ length: columnBuilders.length + 1 }, (_, colIndex) => (
          <Table.Td key={colIndex}>
            <Skeleton height={8} />
          </Table.Td>
        ))}
      </Table.Tr>
    ));
  } else {
    let resources;
    [resources, pagination] = data;
    rows = resources.map((resource: any) => (
      <ResourceTableRow
        key={resource.id}
        resourceName={resourceName}
        resource={resource}
        rowValueBuilders={columnBuilders.map(
          ([_, valueBuilder]) => valueBuilder,
        )}
        resourceDeletionComponentBuilder={resourceDeletionComponentBuilder}
      />
    ));
  }

  return (
    <div>
      <h1>{title}</h1>
      <Group justify="space-between" pb="md">
        <Search name={name} />
        {resourceCreationComponentBuilder && (
          <Link to={addQueryParamToLocation(location, "new")}>
            <Button leftSection={<IconPlus size={"1.3rem"} />}>{name}</Button>
          </Link>
        )}
      </Group>
      <Stack align="center">
        <Table highlightOnHover>
          <Table.Thead>
            <Table.Tr>
              {columnBuilders.map(([name, _], i) => (
                <Table.Th key={i}>{name}</Table.Th>
              ))}
              <Table.Th style={{ textAlign: "right" }}>
                {t("resource.list.actions")}
              </Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>{rows}</Table.Tbody>
        </Table>
        <Pagination
          total={pagination?.total_pages}
          value={pagination?.page}
          onChange={(value) => {
            navigate(
              addQueryParamToLocation(location, "page", value.toString()),
            );
          }}
          py="md"
        />
      </Stack>
      {resourceCreationComponentBuilder &&
        resourceCreationComponentBuilder(newResource)}
      {resourceEditionComponentBuilder(resourceId)}
    </div>
  );
}
