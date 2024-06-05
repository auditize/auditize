import {
  Anchor,
  Badge,
  Box,
  Breadcrumbs,
  Code,
  Group,
  HoverCard,
  Modal,
  Stack,
  Table,
  Text,
  Title,
} from "@mantine/core";
import {
  IconAsterisk,
  IconCalendarClock,
  IconCylinder,
  IconHierarchy,
  IconListDetails,
  IconPaperclip,
  IconRoute,
  IconUser,
} from "@tabler/icons-react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { Breadcrumb } from "rsuite";

import { Section } from "@/components/Section";
import { humanizeDate } from "@/utils/date";
import { titlize } from "@/utils/format";
import { iconSize } from "@/utils/ui";

import { getLog } from "../api";

function KeyValueTable({
  data,
}: {
  data: [React.ReactNode, React.ReactNode][];
}) {
  return (
    <Table withRowBorders={false} verticalSpacing="0.25rem" layout="auto">
      <Table.Tbody>
        {data.map(([name, value], index) => (
          <Table.Tr key={index}>
            <Table.Td width="30%">{name}</Table.Td>
            <Table.Td>{value}</Table.Td>
          </Table.Tr>
        ))}
      </Table.Tbody>
    </Table>
  );
}

function KeyValueSection({
  title,
  icon,
  data,
}: {
  title: string;
  icon: React.ReactNode;
  data?: [React.ReactNode, React.ReactNode][];
}) {
  return (
    data &&
    data.length > 0 && (
      <Section title={title} icon={icon}>
        <KeyValueTable data={data} />
      </Section>
    )
  );
}

function HoverRef({
  value,
  children,
}: {
  value: string;
  children: React.ReactNode;
}) {
  return (
    <HoverCard width={280} shadow="md" openDelay={150} closeDelay={150}>
      <HoverCard.Target>{children}</HoverCard.Target>
      <HoverCard.Dropdown>
        <Text size="sm">
          Ref: <Code>{value}</Code>
        </Text>
      </HoverCard.Dropdown>
    </HoverCard>
  );
}

function Tag({
  value,
}: {
  value: { type: string; name: string | null; ref: string | null };
}) {
  if (value.name && value.ref) {
    return (
      <HoverRef value={value.ref}>
        <Badge
          color="blue"
          rightSection={<IconAsterisk style={iconSize(12)} />}
        >
          {titlize(value.type)}: {value.name}
        </Badge>
      </HoverRef>
    );
  } else {
    return <Badge color="blue">{titlize(value.type)}</Badge>;
  }
}

function NodePath({ value }: { value: { ref: string; name: string }[] }) {
  return (
    <Breadcrumbs separator=">">
      {value.map((node) => (
        <HoverRef value={node.ref} key={node.ref}>
          <Breadcrumb.Item>
            <Anchor underline="never">{node.name}</Anchor>
          </Breadcrumb.Item>
        </HoverRef>
      ))}
    </Breadcrumbs>
  );
}

export function LogDetails({
  repoId,
  logId,
}: {
  repoId?: string;
  logId?: string;
}) {
  const opened = !!(repoId && logId);
  const {
    data: log,
    error,
    isPending,
  } = useQuery({
    queryKey: ["log", logId],
    queryFn: () => getLog(repoId!, logId!),
    enabled: opened,
  });
  const navigate = useNavigate();

  // FIXME: improve loading and error handling

  if (isPending) {
    return null;
  }

  if (error) {
    return <div>{error.message}</div>;
  }

  return (
    <Modal.Root
      size="lg"
      padding="lg"
      opened={opened}
      onClose={() => navigate(-1)}
    >
      <Modal.Overlay />
      <Modal.Content>
        <Modal.Header>
          <Stack>
            <Title order={2}>
              {titlize(log.action.type)}{" "}
              <Text c="dimmed">{titlize(log.action.category)}</Text>
            </Title>
          </Stack>
          <Modal.CloseButton />
        </Modal.Header>
        <Modal.Body>
          <Group mb="lg">
            <IconCalendarClock />
            {humanizeDate(log.savedAt)}
          </Group>
          <Group mb="lg">
            {log.tags.map((tag, index) => (
              <Tag key={index} value={tag} />
            ))}
          </Group>

          <KeyValueSection
            title="Source"
            icon={<IconRoute style={iconSize("1.15rem")} />}
            data={log.source.map(
              (field) =>
                [titlize(field.name), field.value] as [
                  React.ReactNode,
                  React.ReactNode,
                ],
            )}
          />

          <KeyValueSection
            title="Actor"
            icon={<IconUser style={iconSize("1.15rem")} />}
            data={
              log.actor && [
                ["Name", <b>{log.actor.name}</b>],
                ["Type", titlize(log.actor.type)],
                ["Ref", <Code>{log.actor.ref}</Code>],
                ...log.actor.extra.map(
                  (field) =>
                    [titlize(field.name), field.value] as [
                      React.ReactNode,
                      React.ReactNode,
                    ],
                ),
              ]
            }
          />

          <KeyValueSection
            title="Resource"
            icon={<IconCylinder style={iconSize("1.15rem")} />}
            data={
              log.resource && [
                ["Name", <b>{log.resource.name}</b>],
                ["Type", titlize(log.resource.type)],
                ["Ref", <Code>{log.resource.ref}</Code>],
                ...log.resource.extra.map(
                  (field) =>
                    [titlize(field.name), field.value] as [
                      React.ReactNode,
                      React.ReactNode,
                    ],
                ),
              ]
            }
          />

          <KeyValueSection
            title="Details"
            icon={<IconListDetails style={iconSize("1.15rem")} />}
            data={log.details.map(
              (field) =>
                [titlize(field.name), field.value] as [
                  React.ReactNode,
                  React.ReactNode,
                ],
            )}
          />

          <KeyValueSection
            title="Attachments"
            icon={<IconPaperclip style={iconSize("1.15rem")} />}
            data={log.attachments.map(
              (field, index) =>
                [
                  titlize(field.type),
                  <Anchor
                    href={`http://localhost:8000/repos/${repoId}/logs/${log.id}/attachments/${index}`}
                  >
                    {field.description || field.name}
                  </Anchor>,
                ] as [React.ReactNode, React.ReactNode],
            )}
          />

          <Section
            title="Node"
            icon={<IconHierarchy style={iconSize("1.15rem")} />}
          >
            <Box p="xs">
              <NodePath value={log.nodePath} />
            </Box>
          </Section>
        </Modal.Body>
      </Modal.Content>
    </Modal.Root>
  );
}
