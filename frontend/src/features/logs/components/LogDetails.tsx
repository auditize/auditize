import { Accordion, Divider, Modal, Text, Title } from "@mantine/core";
import { IconCylinder, IconHierarchy, IconUser } from "@tabler/icons-react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

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
        <Accordion
          multiple
          defaultValue={["actor", "resource", "node"]}
          variant="default"
        >
          <Accordion.Item key="actor" value="actor">
            <Accordion.Control icon={<IconUser style={iconSize("1.15rem")} />}>
              Actor
            </Accordion.Control>
            <Accordion.Panel>
              {log.actor ? (
                <p>
                  {log.actor.name} ({labelize(log.actor.type)})
                </p>
              ) : null}
            </Accordion.Panel>
          </Accordion.Item>
          <Accordion.Item key="resource" value="resource">
            <Accordion.Control
              icon={<IconCylinder style={iconSize("1.15rem")} />}
            >
              Resource
            </Accordion.Control>
            <Accordion.Panel>
              {log.resource ? (
                <p>
                  {log.resource.name} ({labelize(log.resource.type)})
                </p>
              ) : null}
            </Accordion.Panel>
          </Accordion.Item>
          <Accordion.Item key="node" value="node">
            <Accordion.Control
              icon={<IconHierarchy style={iconSize("1.15rem")} />}
            >
              Node
            </Accordion.Control>
            <Accordion.Panel>
              {log.nodePath.map((node) => node.name).join(" > ")}
            </Accordion.Panel>
          </Accordion.Item>
        </Accordion>
      </div>
    </Modal>
  );
}
