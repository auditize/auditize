import { Anchor, Table } from "@mantine/core";
import { Link, useLocation, useSearchParams } from "react-router-dom";

import { labelize } from "@/utils/format";
import { addQueryParamToLocation } from "@/utils/router";

import { Log } from "../api";
import { LogDetails } from "./LogDetails";

function LogTableRow({
  log,
  onTableFilterChange,
}: {
  log: Log;
  onTableFilterChange: (name: string, value: string) => void;
}) {
  const location = useLocation();
  const logLink = addQueryParamToLocation(location, "log", log.id.toString());

  return (
    <Table.Tr key={log.id}>
      <Table.Td>
        <Anchor component={Link} to={logLink} underline="hover">
          {log.saved_at}
        </Anchor>
      </Table.Td>
      <Table.Td>
        <Anchor
          onClick={() => onTableFilterChange("eventName", log.event.name)}
          underline="hover"
        >
          {labelize(log.event.name)}
        </Anchor>
      </Table.Td>
      <Table.Td>
        <Anchor
          onClick={() =>
            onTableFilterChange("eventCategory", log.event.category)
          }
          underline="hover"
        >
          {labelize(log.event.category)}
        </Anchor>
      </Table.Td>
      <Table.Td>
        {log.actor ? (
          <Anchor
            onClick={() => onTableFilterChange("actorName", log.actor!.name)}
            underline="hover"
          >
            {log.actor.name}
          </Anchor>
        ) : null}
      </Table.Td>
      <Table.Td>
        {log.resource ? (
          <Anchor
            onClick={() =>
              onTableFilterChange("resourceName", log.resource!.name)
            }
            underline="hover"
          >
            {log.resource.name}
          </Anchor>
        ) : null}
      </Table.Td>
      <Table.Td>
        {log.resource ? (
          <Anchor
            onClick={() =>
              onTableFilterChange("resourceType", log.resource!.type)
            }
            underline="hover"
          >
            {log.resource.type}
          </Anchor>
        ) : null}
      </Table.Td>
      <Table.Td>
        {log.node_path
          .map<React.ReactNode>((node) => (
            // FIXME: the filter edition for the node path may not work properly if the selected node
            // has not been already loaded in the TreePicker component
            <Anchor
              key={node.id}
              onClick={() => onTableFilterChange("nodeId", node.id)}
              underline="hover"
            >
              {node.name}
            </Anchor>
          ))
          .reduce((prev, curr) => [prev, " > ", curr])}
      </Table.Td>
    </Table.Tr>
  );
}

export function LogsTable({
  repoId,
  logs,
  footer,
  onTableFilterChange,
}: {
  repoId: string;
  logs: Log[];
  footer: React.ReactNode;
  onTableFilterChange: (name: string, value: string) => void;
}) {
  const [params] = useSearchParams();
  const logId = params.get("log");

  return (
    <>
      <Table>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Date</Table.Th>
            <Table.Th>Event name</Table.Th>
            <Table.Th>Event category</Table.Th>
            <Table.Th>Actor name</Table.Th>
            <Table.Th>Resource name</Table.Th>
            <Table.Th>Resource type</Table.Th>
            <Table.Th>Node</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {logs.map((log) => (
            <LogTableRow
              key={log.id}
              log={log}
              onTableFilterChange={onTableFilterChange}
            />
          ))}
        </Table.Tbody>
        <Table.Tfoot>
          <Table.Tr>
            <Table.Th colSpan={7}>{footer}</Table.Th>
          </Table.Tr>
        </Table.Tfoot>
      </Table>
      <LogDetails repoId={repoId} logId={logId || undefined} />
    </>
  );
}
