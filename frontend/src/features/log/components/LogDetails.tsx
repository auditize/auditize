import {
  Anchor,
  Badge,
  Box,
  Breadcrumbs,
  Code,
  Flex,
  Group,
  Modal,
  ScrollArea,
  Skeleton,
  Stack,
  Table,
  Text,
  Title,
  Tooltip,
} from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import {
  IconCalendarClock,
  IconCylinder,
  IconHierarchy,
  IconListDetails,
  IconPaperclip,
  IconRoute,
  IconTags,
  IconUser,
} from "@tabler/icons-react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { Section } from "@/components/Section";
import { SectionExpand } from "@/components/Section/Section";
import { humanizeDate } from "@/utils/date";
import { iconBesideText } from "@/utils/ui";

import { getLog, Log } from "../api";
import { useLogNavigationState } from "./LogNavigationState";
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
            <Table.Td width="35%" pl="1.25rem" style={{ verticalAlign: "top" }}>
              {name}
            </Table.Td>
            <Table.Td style={{ verticalAlign: "top" }}>{value}</Table.Td>
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

function ExpandableSection({
  title,
  icon,
  renderNotExpanded,
  renderExpanded,
}: {
  title: string;
  icon: React.ReactNode;
  renderNotExpanded: () => React.ReactNode;
  renderExpanded: () => React.ReactNode;
}) {
  const [expanded, { toggle }] = useDisclosure(false);

  return (
    <Section
      title={title}
      icon={icon}
      rightSection={<SectionExpand expanded={expanded} toggle={toggle} />}
    >
      {expanded ? renderExpanded() : renderNotExpanded()}
    </Section>
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
      <Badge>
        {logTranslator("tag_type", value.type)}: {value.name}
      </Badge>
    );
  } else {
    return <Badge>{logTranslator("tag_type", value.type)}</Badge>;
  }
}

function LogEntitySection({ log }: { log: Log }) {
  const { t } = useTranslation();

  return (
    <ExpandableSection
      title={t("log.entity")}
      icon={
        <IconHierarchy style={iconBesideText({ size: "18px", top: "0px" })} />
      }
      renderNotExpanded={() => (
        <Breadcrumbs separator=">" p="0px" pl="1.25rem" pt="0.5rem">
          {log.entityPath.map((entity) => (
            <Text size="sm" key={entity.ref}>
              {entity.name}
            </Text>
          ))}
        </Breadcrumbs>
      )}
      renderExpanded={() => (
        <KeyValueTable
          data={log.entityPath.map((entity) => [
            entity.name,
            <Code>{entity.ref}</Code>,
          ])}
        />
      )}
    />
  );
}

function LogTagSection({ log, repoId }: { log: Log; repoId: string }) {
  const { t } = useTranslation();
  const logTranslator = useLogTranslator(repoId);

  return (
    log.tags.length > 0 && (
      <ExpandableSection
        title={t("log.tags")}
        icon={<IconTags style={iconBesideText({ size: "18px", top: "0px" })} />}
        renderNotExpanded={() => (
          <Group pl="1.25rem" pt="0.5rem">
            {log.tags.map((tag, index) => (
              <Tag key={index} value={tag} repoId={repoId} />
            ))}
          </Group>
        )}
        renderExpanded={() => (
          <KeyValueTable
            data={log.tags.map((tag) =>
              tag.name && tag.ref
                ? [
                    <Text size="sm">
                      {logTranslator("tag_type", tag.type)}: <b>{tag.name}</b>
                    </Text>,
                    <Code>{tag.ref}</Code>,
                  ]
                : [
                    <Text size="sm">
                      {logTranslator("tag_type", tag.type)}
                    </Text>,
                    null,
                  ],
            )}
          />
        )}
      />
    )
  );
}

function LogSourceSection({ log, repoId }: { log: Log; repoId: string }) {
  const { t } = useTranslation();
  const logTranslator = useLogTranslator(repoId);
  return (
    <KeyValueSection
      title={t("log.source")}
      icon={<IconRoute style={iconBesideText({ size: "18px", top: "0px" })} />}
      data={log.source.map(
        (field) =>
          [logTranslator("source_field", field.name), field.value] as [
            React.ReactNode,
            React.ReactNode,
          ],
      )}
    />
  );
}

function LogActorSection({ log, repoId }: { log: Log; repoId: string }) {
  const { t } = useTranslation();
  const logTranslator = useLogTranslator(repoId);

  return (
    <KeyValueSection
      title={t("log.actor")}
      icon={<IconUser style={iconBesideText({ size: "18px", top: "-1px" })} />}
      data={
        log.actor && [
          [t("log.view.name"), <b>{log.actor.name}</b>],
          [t("log.view.type"), logTranslator("actor_type", log.actor.type)],
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
  );
}

function LogResourceSection({ log, repoId }: { log: Log; repoId: string }) {
  const { t } = useTranslation();
  const logTranslator = useLogTranslator(repoId);

  return (
    <KeyValueSection
      title={t("log.resource")}
      icon={
        <IconCylinder style={iconBesideText({ size: "18px", top: "0px" })} />
      }
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
  );
}

function LogDetailsSection({ log, repoId }: { log: Log; repoId: string }) {
  const { t } = useTranslation();
  const logTranslator = useLogTranslator();

  return (
    <KeyValueSection
      title={t("log.details")}
      icon={
        <IconListDetails style={iconBesideText({ size: "18px", top: "0px" })} />
      }
      data={log.details.map(
        (field) =>
          [logTranslator("detail_field", field.name), field.value] as [
            React.ReactNode,
            React.ReactNode,
          ],
      )}
    />
  );
}

function LogAttachmentSection({ log, repoId }: { log: Log; repoId: string }) {
  const { t } = useTranslation();
  const logTranslator = useLogTranslator(repoId);
  const baseURL = window.auditizeBaseURL ?? "";

  return (
    <KeyValueSection
      title={t("log.attachment")}
      icon={
        <IconPaperclip style={iconBesideText({ size: "18px", top: "0px" })} />
      }
      data={log.attachments.map(
        (field, index) =>
          [
            logTranslator("attachment_type", field.type),
            <Tooltip
              label={t("log.downloadAttachment")}
              withArrow
              withinPortal={false}
            >
              <Anchor
                href={`${baseURL}/api/repos/${repoId}/logs/${log.id}/attachments/${index}`}
                size="sm"
              >
                {field.name}
              </Anchor>
            </Tooltip>,
          ] as [React.ReactNode, React.ReactNode],
      )}
    />
  );
}

function LogDate({ log }: { log: Log }) {
  return (
    <Group mb="lg" gap="0">
      <IconCalendarClock
        style={iconBesideText({
          size: "16px",
          marginRight: "0.25rem",
        })}
      />
      <Text size="sm">{humanizeDate(log.savedAt)}</Text>
    </Group>
  );
}

function LogDetailsHeaderSkeleton() {
  return (
    <Stack w="500px" gap="xs">
      <Skeleton height={16} width="100%" />
      <Skeleton height={10} width="80%" />
      <Skeleton height={10} width="40%" />
    </Stack>
  );
}

function LogDetailsBodySkeleton() {
  return (
    <>
      {Array.from({ length: 4 }).map((_, i) => (
        <Box key={i} p="xs">
          <Skeleton height={12} width="30%" />
          <Skeleton height={1} width="100%" my="xs" />
          <Table withRowBorders={false}>
            <Table.Tbody>
              {Array.from({ length: 3 }).map((_, j) => (
                <Table.Tr key={j}>
                  <Table.Td width="35%">
                    <Skeleton height={10} width="100%" />
                  </Table.Td>
                  <Table.Td>
                    <Skeleton height={10} width="100%" />
                  </Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        </Box>
      ))}
    </>
  );
}

export function LogDetails({ repoId }: { repoId?: string }) {
  const { t } = useTranslation();
  const logTranslator = useLogTranslator(repoId);
  const { displayedLogId, setDisplayedLogId } = useLogNavigationState();
  const logQuery = useQuery({
    queryKey: ["log", repoId, displayedLogId],
    queryFn: () => getLog(repoId!, displayedLogId!),
    enabled: displayedLogId !== null,
  });
  const log = logQuery.data;

  // FIXME: improve error handling
  if (logQuery.error) {
    return <div>{logQuery.error.message}</div>;
  }

  return (
    <Modal.Root
      size="lg"
      padding="lg"
      opened={displayedLogId !== null}
      onClose={() => setDisplayedLogId(null)}
      withinPortal={false}
      scrollAreaComponent={ScrollArea.Autosize}
    >
      <Modal.Overlay />
      <Modal.Content>
        <Modal.Header>
          <Flex justify="space-between" w="100%">
            <Stack gap="0.5rem">
              {log ? (
                <>
                  <div>
                    <Tooltip label={t("log.actionType")} withinPortal={false}>
                      <Title order={2}>
                        {logTranslator("action_type", log.action.type)}
                      </Title>
                    </Tooltip>
                    <Tooltip
                      label={t("log.actionCategory")}
                      withinPortal={false}
                    >
                      <Text c="dimmed" style={{ display: "inline-block" }}>
                        {logTranslator("action_category", log.action.category)}
                      </Text>
                    </Tooltip>
                  </div>
                  <LogDate log={log} />
                </>
              ) : (
                <LogDetailsHeaderSkeleton />
              )}
            </Stack>
            <Modal.CloseButton />
          </Flex>
        </Modal.Header>
        <Modal.Body>
          <Stack gap="1rem">
            {log ? (
              <>
                <LogTagSection log={log} repoId={repoId!} />
                <LogSourceSection log={log} repoId={repoId!} />
                <LogActorSection log={log} repoId={repoId!} />
                <LogResourceSection log={log} repoId={repoId!} />
                <LogDetailsSection log={log} repoId={repoId!} />
                <LogAttachmentSection log={log} repoId={repoId!} />
                <LogEntitySection log={log} />
              </>
            ) : (
              <LogDetailsBodySkeleton />
            )}
          </Stack>
        </Modal.Body>
      </Modal.Content>
    </Modal.Root>
  );
}
