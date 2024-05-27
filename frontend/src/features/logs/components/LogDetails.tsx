import { Code, Divider, Modal, Table, Text } from "@mantine/core";
import { IconCylinder, IconHierarchy, IconUser } from "@tabler/icons-react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { Section } from "@/components/Section";
import { labelize } from "@/utils/format";
import { iconSize } from "@/utils/ui";

import { getLog } from "../api";

function DataTable({ data }: { data: [React.ReactNode, React.ReactNode][] }) {
  return (
    <Table withRowBorders={false} verticalSpacing="0.25rem" layout="auto">
      {data.map(([name, value], index) => (
        <Table.Tr key={index}>
          <Table.Td>{name}</Table.Td>
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
            <Table
              withRowBorders={false}
              verticalSpacing="0.25rem"
              layout="auto"
            >
              <Table.Tr>
                <Table.Td>Name</Table.Td>
                <Table.Td>
                  <b>{log.actor.name}</b>
                </Table.Td>
              </Table.Tr>
              <Table.Tr>
                <Table.Td width="30%">Type</Table.Td>
                <Table.Td>{labelize(log.actor.type)}</Table.Td>
              </Table.Tr>
              <Table.Tr>
                <Table.Td>Ref</Table.Td>
                <Table.Td>
                  <Code>{log.actor.ref}</Code>
                </Table.Td>
              </Table.Tr>
              {log.actor.extra.map((field) => (
                <Table.Tr key={field.name}>
                  <Table.Td>{labelize(field.name)}</Table.Td>
                  <Table.Td>{field.value}</Table.Td>
                </Table.Tr>
              ))}
            </Table>
          </Section>
        )}
        {log.resource && (
          <Section
            title="Resource"
            icon={<IconCylinder style={iconSize("1.15rem")} />}
          >
            <Table
              withRowBorders={false}
              verticalSpacing="0.25rem"
              layout="auto"
            >
              <Table.Tr>
                <Table.Td>Name</Table.Td>
                <Table.Td>
                  <b>{log.resource.name}</b>
                </Table.Td>
              </Table.Tr>
              <Table.Tr>
                <Table.Td width="30%">Type</Table.Td>
                <Table.Td>{labelize(log.resource.type)}</Table.Td>
              </Table.Tr>
              <Table.Tr>
                <Table.Td>Ref</Table.Td>
                <Table.Td>
                  <Code>{log.resource.ref}</Code>
                </Table.Td>
              </Table.Tr>
              {log.resource.extra.map((field) => (
                <Table.Tr key={field.name}>
                  <Table.Td>{labelize(field.name)}</Table.Td>
                  <Table.Td>{field.value}</Table.Td>
                </Table.Tr>
              ))}
            </Table>
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
