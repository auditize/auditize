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
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { Breadcrumb } from "rsuite";

import { Section } from "@/components/Section";
import { humanizeDate } from "@/utils/date";
import { titlize } from "@/utils/format";
import { iconSize } from "@/utils/ui";

import { getLog } from "../api";
import { useLogContext } from "../context";
import { useLogTranslator } from "./LogTranslation";

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
  const { t } = useTranslation();
  return (
    <HoverCard width={280} shadow="md" openDelay={150} closeDelay={150}>
      <HoverCard.Target>{children}</HoverCard.Target>
      <HoverCard.Dropdown>
        <Text size="sm">
          {t("log.view.ref")}: <Code>{value}</Code>
        </Text>
      </HoverCard.Dropdown>
    </HoverCard>
  );
}

function Tag({
  value,
  repoId,
}: {
  value: { type: string; name: string | null; ref: string | null };
  repoId: string;
}) {
  const logTranslator = useLogTranslator(repoId);

  if (value.name && value.ref) {
    return (
      <HoverRef value={value.ref}>
        <Badge
          color="blue"
          rightSection={<IconAsterisk style={iconSize(12)} />}
        >
          {logTranslator("tag_type", value.type)}: {value.name}
        </Badge>
      </HoverRef>
    );
  } else {
    return <Badge color="blue">{logTranslator("tag_type", value.type)}</Badge>;
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

export function LogDetails({ repoId }: { repoId?: string }) {
  const { t } = useTranslation();
  const logTranslator = useLogTranslator(repoId);
  const { displayedLogId, setDisplayedLogId } = useLogContext();
  const {
    data: log,
    error,
    isPending,
  } = useQuery({
    queryKey: ["log", repoId, displayedLogId],
    queryFn: () => getLog(repoId!, displayedLogId!),
    enabled: displayedLogId !== null,
  });

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
      opened={displayedLogId !== null}
      onClose={() => setDisplayedLogId(null)}
      withinPortal={false}
    >
      <Modal.Overlay />
      <Modal.Content>
        <Modal.Header>
          <Stack>
            <Title order={2}>
              {logTranslator("action_type", log.action.type)}{" "}
              <Text c="dimmed">
                {logTranslator("action_category", log.action.category)}
              </Text>
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
              <Tag key={index} value={tag} repoId={repoId!} />
            ))}
          </Group>

          <KeyValueSection
            title={t("log.source")}
            icon={<IconRoute style={iconSize("1.15rem")} />}
            data={log.source.map(
              (field) =>
                [logTranslator("source_field", field.name), field.value] as [
                  React.ReactNode,
                  React.ReactNode,
                ],
            )}
          />

          <KeyValueSection
            title={t("log.actor")}
            icon={<IconUser style={iconSize("1.15rem")} />}
            data={
              log.actor && [
                [t("log.view.name"), <b>{log.actor.name}</b>],
                [
                  t("log.view.type"),
                  logTranslator("actor_type", log.actor.type),
                ],
                [t("log.view.ref"), <Code>{log.actor.ref}</Code>],
                ...log.actor.extra.map(
                  (field) =>
                    [
                      logTranslator("actor_custom_field", field.name),
                      field.value,
                    ] as [React.ReactNode, React.ReactNode],
                ),
              ]
            }
          />

          <KeyValueSection
            title={t("log.resource")}
            icon={<IconCylinder style={iconSize("1.15rem")} />}
            data={
              log.resource && [
                [t("log.view.name"), <b>{log.resource.name}</b>],
                [
                  t("log.view.type"),
                  logTranslator("resource_type", log.resource.type),
                ],
                [t("log.view.ref"), <Code>{log.resource.ref}</Code>],
                ...log.resource.extra.map(
                  (field) =>
                    [
                      logTranslator("resource_custom_field", field.name),
                      field.value,
                    ] as [React.ReactNode, React.ReactNode],
                ),
              ]
            }
          />

          <KeyValueSection
            title={t("log.details")}
            icon={<IconListDetails style={iconSize("1.15rem")} />}
            data={log.details.map(
              (field) =>
                [logTranslator("detail_field", field.name), field.value] as [
                  React.ReactNode,
                  React.ReactNode,
                ],
            )}
          />

          <KeyValueSection
            title={t("log.attachment")}
            icon={<IconPaperclip style={iconSize("1.15rem")} />}
            data={log.attachments.map(
              (field, index) =>
                [
                  logTranslator("attachment_type", field.type),
                  <Anchor
                    href={`/api/repos/${repoId}/logs/${log.id}/attachments/${index}`}
                  >
                    {field.description || field.name}
                  </Anchor>,
                ] as [React.ReactNode, React.ReactNode],
            )}
          />

          <Section
            title={t("log.node")}
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
