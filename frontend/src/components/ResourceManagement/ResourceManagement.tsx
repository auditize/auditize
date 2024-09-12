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
  Title,
} from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import { IconPlus, IconSearch } from "@tabler/icons-react";
import { useQuery } from "@tanstack/react-query";
import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import { iconSize } from "@/utils/ui";

import { ApiErrorMessage } from "../ErrorMessage";
import { useResourceManagementState } from "./ResourceManagementState";

type ResourceCreationComponentBuilder = (
  opened: boolean,
  onClose: () => void,
) => React.ReactNode;
type ResourceEditionComponentBuilder = (
  resourceId: string | null,
  onClose: () => void,
) => React.ReactNode;
type ResourceDeletionComponentBuilder = (
  resource: any,
  opened: boolean,
  onClose: () => void,
) => React.ReactNode;

function ResourceTableRow({
  resource,
  onClick,
  link,
  columnDefinitions,
  resourceDeletionComponentBuilder,
}: {
  resource: any;
  onClick: () => void;
  link?: string;
  columnDefinitions: ColumnDefinition[];
  resourceDeletionComponentBuilder: ResourceDeletionComponentBuilder;
}) {
  const { t } = useTranslation();
  const [opened, { open, close }] = useDisclosure();

  const deletionConfirmModal = resourceDeletionComponentBuilder(
    resource,
    opened,
    close,
  );

  return (
    <Table.Tr>
      {columnDefinitions.map(([_, builder, style], i) => (
        <Table.Td key={i} style={style}>
          {builder(resource)}
        </Table.Td>
      ))}
      <Table.Td style={{ textAlign: "right" }}>
        <Group justify="flex-end" gap={"md"}>
          {link ? (
            <Anchor component={Link} to={link}>
              {t("resource.list.edit")}
            </Anchor>
          ) : (
            <Anchor component="a" onClick={onClick}>
              {t("resource.list.edit")}
            </Anchor>
          )}
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

function Search({
  value,
  onChange,
}: {
  value: string;
  onChange: (value: string) => void;
}) {
  const { t } = useTranslation();
  const [search, setSearch] = useState("");
  const handleSearch = () => onChange(search);

  useEffect(() => {
    setSearch(value);
  }, [value]);

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
            <IconSearch style={iconSize(22)} />
          )
        }
      />
      <Button onClick={handleSearch} disabled={!search && !value}>
        {t("resource.list.search")}
      </Button>
    </Group>
  );
}

type ColumnDefinition =
  | [string, (resource: any) => React.ReactNode]
  | [string, (resource: any) => React.ReactNode, React.CSSProperties];

export function ResourceManagement({
  title,
  name,
  stateMode = "url",
  queryKey,
  queryFn,
  columnDefinitions,
  resourceCreationComponentBuilder,
  resourceEditionComponentBuilder,
  resourceDeletionComponentBuilder,
}: {
  title: React.ReactNode;
  name: string;
  stateMode?: "url" | "useState";
  queryKey: (search: string | null, page: number) => any[];
  queryFn: (search: string | null, page: number) => () => Promise<any>;
  columnDefinitions: ColumnDefinition[];
  resourceCreationComponentBuilder?: ResourceCreationComponentBuilder;
  resourceEditionComponentBuilder: ResourceEditionComponentBuilder;
  resourceDeletionComponentBuilder: ResourceDeletionComponentBuilder;
}) {
  const { t } = useTranslation();
  const {
    page,
    setPage,
    isNew,
    setIsNew,
    resourceId,
    setResourceId,
    resourceLink,
    search,
    setSearch,
  } = useResourceManagementState(stateMode);
  const resourcesQuery = useQuery({
    queryKey: queryKey(search, page),
    queryFn: queryFn(search, page),
  });

  if (resourcesQuery.error) {
    return <ApiErrorMessage error={resourcesQuery.error} />;
  }

  let rows;
  let pagination;
  if (resourcesQuery.isPending) {
    rows = Array.from({ length: 10 }).map((_, rowIndex) => (
      <Table.Tr key={rowIndex} style={{ height: "2rem" }}>
        {Array.from({ length: columnDefinitions.length + 1 }, (_, colIndex) => (
          <Table.Td key={colIndex}>
            <Skeleton height={8} />
          </Table.Td>
        ))}
      </Table.Tr>
    ));
  } else {
    let resources;
    [resources, pagination] = resourcesQuery.data;
    rows = resources.map((resource: any) => (
      <ResourceTableRow
        key={resource.id}
        onClick={() => setResourceId(resource.id)}
        link={resourceLink ? resourceLink(resource.id) : undefined}
        resource={resource}
        columnDefinitions={columnDefinitions}
        resourceDeletionComponentBuilder={resourceDeletionComponentBuilder}
      />
    ));
  }

  return (
    <div>
      <Title order={1} pb="xl">
        {title}
      </Title>
      <Group justify="space-between" pb="md">
        <Search value={search} onChange={setSearch} />
        {resourceCreationComponentBuilder && (
          <Button
            onClick={() => setIsNew(true)}
            leftSection={<IconPlus size={"1.3rem"} />}
          >
            {name}
          </Button>
        )}
      </Group>
      <Stack align="center">
        <Table highlightOnHover>
          <Table.Thead>
            <Table.Tr>
              {columnDefinitions.map(([name, _], i) => (
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
          onChange={setPage}
          py="md"
        />
      </Stack>
      {resourceCreationComponentBuilder &&
        resourceCreationComponentBuilder(isNew, () => setIsNew(false))}
      {resourceEditionComponentBuilder(resourceId, () => setResourceId(null))}
    </div>
  );
}
