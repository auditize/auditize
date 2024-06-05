import { Anchor, Stack } from "@mantine/core";
import { DataTable } from "mantine-datatable";
import { Link, useLocation, useSearchParams } from "react-router-dom";

import { humanizeDate } from "@/utils/date";
import { labelize } from "@/utils/format";
import { addQueryParamToLocation } from "@/utils/router";

import { Log } from "../api";
import { LogDetails } from "./LogDetails";

function DateField({ log }: { log: Log }) {
  const location = useLocation();
  const logLink = addQueryParamToLocation(location, "log", log.id.toString());

  return (
    <Anchor component={Link} to={logLink} underline="hover">
      {humanizeDate(log.savedAt)}
    </Anchor>
  );
}

function ActorField({
  log,
  onTableFilterChange,
}: {
  log: Log;
  onTableFilterChange: (name: string, value: string) => void;
}) {
  return log.actor ? (
    <Anchor
      onClick={() => onTableFilterChange("actorRef", log.actor!.ref)}
      underline="hover"
    >
      {log.actor.name}
    </Anchor>
  ) : null;
}

function ActionTypeField({
  log,
  onTableFilterChange,
}: {
  log: Log;
  onTableFilterChange: (name: string, value: string) => void;
}) {
  return (
    <Anchor
      onClick={() => onTableFilterChange("actionType", log.action.type)}
      underline="hover"
    >
      {labelize(log.action.type)}
    </Anchor>
  );
}

function ActionCategoryField({
  log,
  onTableFilterChange,
}: {
  log: Log;
  onTableFilterChange: (name: string, value: string) => void;
}) {
  return (
    <Anchor
      onClick={() => onTableFilterChange("actionCategory", log.action.category)}
      underline="hover"
    >
      {labelize(log.action.category)}
    </Anchor>
  );
}

function ResourceField({
  log,
  onTableFilterChange,
}: {
  log: Log;
  onTableFilterChange: (name: string, value: string) => void;
}) {
  return log.resource ? (
    <Anchor
      onClick={() => onTableFilterChange("resourceRef", log.resource!.ref)}
      underline="hover"
    >
      {log.resource.name}
    </Anchor>
  ) : null;
}

function ResourceTypeField({
  log,
  onTableFilterChange,
}: {
  log: Log;
  onTableFilterChange: (name: string, value: string) => void;
}) {
  return log.resource ? (
    <Anchor
      onClick={() => onTableFilterChange("resourceType", log.resource!.type)}
      underline="hover"
    >
      {labelize(log.resource.type)}
    </Anchor>
  ) : null;
}

function NodePathField({
  log,
  onTableFilterChange,
}: {
  log: Log;
  onTableFilterChange: (name: string, value: string) => void;
}) {
  return log.nodePath
    .map<React.ReactNode>((node) => (
      <Anchor
        key={node.ref}
        onClick={() => onTableFilterChange("nodeRef", node.ref)}
        underline="hover"
      >
        {node.name}
      </Anchor>
    ))
    .reduce((prev, curr) => [prev, " > ", curr]);
}

export function LogTable({
  repoId,
  logs,
  isLoading,
  footer,
  onTableFilterChange,
}: {
  repoId: string;
  logs?: Log[];
  isLoading: boolean;
  footer: React.ReactNode;
  onTableFilterChange: (name: string, value: string) => void;
}) {
  const [params] = useSearchParams();
  const logId = params.get("log");

  let columns = [
    {
      accessor: "savedAt",
      title: "Date",
      render: (log: Log) => <DateField log={log} />,
    },
    {
      accessor: "actorRef",
      title: "Actor",
      render: (log: Log) => (
        <ActorField log={log} onTableFilterChange={onTableFilterChange} />
      ),
    },
    {
      accessor: "actionType",
      title: "Action type",
      render: (log: Log) => (
        <ActionTypeField log={log} onTableFilterChange={onTableFilterChange} />
      ),
    },
    {
      accessor: "actionCategory",
      title: "Action category",
      render: (log: Log) => (
        <ActionCategoryField
          log={log}
          onTableFilterChange={onTableFilterChange}
        />
      ),
    },
    {
      accessor: "resource",
      title: "Resource",
      render: (log: Log) => (
        <ResourceField log={log} onTableFilterChange={onTableFilterChange} />
      ),
    },
    {
      accessor: "resourceType",
      title: "Resource type",
      render: (log: Log) => (
        <ResourceTypeField
          log={log}
          onTableFilterChange={onTableFilterChange}
        />
      ),
    },
    {
      accessor: "nodePath",
      title: "Node",
      render: (log: Log) => (
        <NodePathField log={log} onTableFilterChange={onTableFilterChange} />
      ),
    },
  ];

  return (
    <>
      <Stack>
        <DataTable
          columns={columns}
          records={logs}
          fetching={isLoading}
          minHeight={150}
          noRecordsText="No logs found"
        />
        {logs && logs.length > 0 && footer}
      </Stack>
      <LogDetails repoId={repoId} logId={logId || undefined} />
    </>
  );
}
