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
          {log.savedAt}
        </Anchor>
      </Table.Td>
      <Table.Td>
        <Anchor
          onClick={() => onTableFilterChange("actionType", log.action.type)}
          underline="hover"
        >
          {labelize(log.action.type)}
        </Anchor>
      </Table.Td>
      <Table.Td>
        <Anchor
          onClick={() =>
            onTableFilterChange("actionCategory", log.action.category)
          }
          underline="hover"
        >
          {labelize(log.action.category)}
        </Anchor>
      </Table.Td>
      <Table.Td>
        {log.actor ? (
          <Anchor
            onClick={() => onTableFilterChange("actorRef", log.actor!.ref)}
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
              onTableFilterChange("resourceRef", log.resource!.ref)
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
        {log.nodePath
          .map<React.ReactNode>((node) => (
            // FIXME: the filter edition for the node path may not work properly if the selected node
            // has not been already loaded in the TreePicker component
            <Anchor
              key={node.ref}
              onClick={() => onTableFilterChange("nodeRef", node.ref)}
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
            <Table.Th>Action type</Table.Th>
            <Table.Th>Action category</Table.Th>
            <Table.Th>Actor</Table.Th>
            <Table.Th>Resource</Table.Th>
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
