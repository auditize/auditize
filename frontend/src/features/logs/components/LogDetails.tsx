import { iconSize } from '@/utils/ui';

import { labelize } from "@/utils/format";
import { Modal, Title, Text, Divider, Accordion } from "@mantine/core";
import { IconUser, IconCylinder, IconHierarchy } from "@tabler/icons-react";


export function LogDetails({ log, opened, onClose }: { log: Log; opened: boolean; onClose: () => void; }) {
  return (
    <Modal
      title={"Log details"} size="lg" padding="lg"
      opened={opened} onClose={onClose}
    >
      <div>
        <table>
          <tbody>
            <tr>
              <td><Text fw={700}>Date</Text></td>
              <td>{log.saved_at}</td>
            </tr>
            <tr>
              <td><Text fw={700}>Event name</Text></td>
              <td>{labelize(log.event.name)}</td>
            </tr>
            <tr>
              <td><Text fw={700}>Event category</Text></td>
              <td>{labelize(log.event.category)}</td>
            </tr>
          </tbody>
        </table>
        <Divider my="md" size="md" color="blue" />
        <Accordion multiple defaultValue={["actor", "resource", "node"]} variant='default'>
          <Accordion.Item key="actor" value="actor">
            <Accordion.Control icon={<IconUser style={iconSize("1.15rem")} />}>
              Actor
            </Accordion.Control>
            <Accordion.Panel>
              {log.actor ?
                <p>{log.actor.name} ({labelize(log.actor.type)})</p> :
                null}
            </Accordion.Panel>
          </Accordion.Item>
          <Accordion.Item key="resource" value="resource">
            <Accordion.Control icon={<IconCylinder style={iconSize("1.15rem")} />}>
              Resource
            </Accordion.Control>
            <Accordion.Panel>
              {log.resource ?
                <p>{log.resource.name} ({labelize(log.resource.type)})</p> :
                null}
            </Accordion.Panel>
          </Accordion.Item>
          <Accordion.Item key="node" value="node">
            <Accordion.Control icon={<IconHierarchy style={iconSize("1.15rem")} />}>
              Node
            </Accordion.Control>
            <Accordion.Panel>
              {log.node_path.map((node) => node.name).join(' > ')}
            </Accordion.Panel>
          </Accordion.Item>
        </Accordion>
      </div>
    </Modal>
  );
}
