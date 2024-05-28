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
  IconRoute,
  IconUser,
} from "@tabler/icons-react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { Breadcrumb } from "rsuite";

import { Section } from "@/components/Section";
import { humanizeDate } from "@/utils/date";
import { labelize } from "@/utils/format";
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
          {labelize(value.type)}: {value.name}
        </Badge>
      </HoverRef>
    );
  } else {
    return <Badge color="blue">{labelize(value.type)}</Badge>;
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
              {labelize(log.action.type)}{" "}
              <Text c="dimmed">{labelize(log.action.category)}</Text>
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

          {log.source && (
            <Section
              title="Source"
              icon={<IconRoute style={iconSize("1.15rem")} />}
            >
              <KeyValueTable
                data={log.source.map(
                  (field) =>
                    [labelize(field.name), field.value] as [
                      React.ReactNode,
                      React.ReactNode,
                    ],
                )}
              />
            </Section>
          )}

          <div>
            {log.actor && (
              <Section
                title="Actor"
                icon={<IconUser style={iconSize("1.15rem")} />}
              >
                <KeyValueTable
                  data={[
                    ["Name", <b>{log.actor.name}</b>],
                    ["Type", labelize(log.actor.type)],
                    ["Ref", <Code>{log.actor.ref}</Code>],
                    ...log.actor.extra.map(
                      (field) =>
                        [labelize(field.name), field.value] as [
                          React.ReactNode,
                          React.ReactNode,
                        ],
                    ),
                  ]}
                />
              </Section>
            )}
            {log.resource && (
              <Section
                title="Resource"
                icon={<IconCylinder style={iconSize("1.15rem")} />}
              >
                <KeyValueTable
                  data={[
                    ["Name", <b>{log.resource.name}</b>],
                    ["Type", labelize(log.resource.type)],
                    ["Ref", <Code>{log.resource.ref}</Code>],
                    ...log.resource.extra.map(
                      (field) =>
                        [labelize(field.name), field.value] as [
                          React.ReactNode,
                          React.ReactNode,
                        ],
                    ),
                  ]}
                />
              </Section>
            )}
            {log.details && (
              <Section
                title="Details"
                icon={<IconListDetails style={iconSize("1.15rem")} />}
              >
                <KeyValueTable
                  data={log.details.map(
                    (field) =>
                      [labelize(field.name), field.value] as [
                        React.ReactNode,
                        React.ReactNode,
                      ],
                  )}
                />
              </Section>
            )}
            <Section
              title="Node"
              icon={<IconHierarchy style={iconSize("1.15rem")} />}
            >
              <Box p="xs">
                <NodePath value={log.nodePath} />
              </Box>
            </Section>
          </div>
        </Modal.Body>
      </Modal.Content>
    </Modal.Root>
  );
}
