import { Divider, Modal, Text } from "@mantine/core";
import { IconCylinder, IconHierarchy, IconUser } from "@tabler/icons-react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { Section } from "@/components/Section";
import { labelize } from "@/utils/format";
import { iconSize } from "@/utils/ui";

import { getLog } from "../api";

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
        <Section title="Actor" icon={<IconUser style={iconSize("1.15rem")} />}>
          {log.actor ? (
            <p>
              {log.actor.name} ({labelize(log.actor.type)})
            </p>
          ) : null}
        </Section>
        <Section
          title="Resource"
          icon={<IconCylinder style={iconSize("1.15rem")} />}
        >
          {log.resource ? (
            <p>
              {log.resource.name} ({labelize(log.resource.type)})
            </p>
          ) : null}
        </Section>
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
