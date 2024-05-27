import { Code, Divider, Modal, Table, Text } from "@mantine/core";
import { IconCylinder, IconHierarchy, IconUser } from "@tabler/icons-react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { Section } from "@/components/Section";
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
      title={"Log details"}
      size="lg"
      padding="lg"
      opened={opened}
      onClose={() => navigate(-1)}
    >
      <div>
        <table>
          <tbody>
            <tr>
              <td>
                <Text fw={700}>Date</Text>
              </td>
              <td>{log.savedAt}</td>
            </tr>
            <tr>
              <td>
                <Text fw={700}>Action type</Text>
              </td>
              <td>{labelize(log.action.type)}</td>
            </tr>
            <tr>
              <td>
                <Text fw={700}>Action category</Text>
              </td>
              <td>{labelize(log.action.category)}</td>
            </tr>
          </tbody>
        </table>
        <Divider my="md" size="md" color="blue" />
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
