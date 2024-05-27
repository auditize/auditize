import {
  Badge,
  Code,
  Group,
  HoverCard,
  Modal,
  Table,
  Text,
  Title,
} from "@mantine/core";
import {
  IconCalendarClock,
  IconCylinder,
  IconHierarchy,
  IconListDetails,
  IconRoute,
  IconUser,
} from "@tabler/icons-react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

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
      {data.map(([name, value], index) => (
        <Table.Tr key={index}>
          <Table.Td width="30%">{name}</Table.Td>
          <Table.Td>{value}</Table.Td>
        </Table.Tr>
      ))}
    </Table>
  );
}

function Tag({
  value,
}: {
  value: { type: string; name: string | null; ref: string | null };
}) {
  if (value.name && value.ref) {
    return (
      <HoverCard width={280} shadow="md">
        <HoverCard.Target>
          <Badge color="blue">
            {labelize(value.type)}: {value.name}
          </Badge>
        </HoverCard.Target>
        <HoverCard.Dropdown>
          <Text size="sm">
            Ref: <Code>{value.ref}</Code>
          </Text>
        </HoverCard.Dropdown>
      </HoverCard>
    );
  } else {
    return <Badge color="blue">{labelize(value.type)}</Badge>;
  }
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
    <Modal
      title={
        <Title order={3} size="h2">
          {labelize(log.action.type)} ({labelize(log.action.category)})
        </Title>
      }
      size="lg"
      padding="lg"
      opened={opened}
      onClose={() => navigate(-1)}
    >
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
          <p>{log.nodePath.map((node) => node.name).join(" > ")}</p>
        </Section>
      </div>
    </Modal>
  );
}
