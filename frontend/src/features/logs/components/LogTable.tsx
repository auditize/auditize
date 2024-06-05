import { Anchor, Stack, Text } from "@mantine/core";
import { DataTable } from "mantine-datatable";
import { useLocation, useNavigate, useSearchParams } from "react-router-dom";

import { humanizeDate } from "@/utils/date";
import { labelize } from "@/utils/format";
import { addQueryParamToLocation } from "@/utils/router";

import { Log } from "../api";
import { LogDetails } from "./LogDetails";

function InlineFilterLink({
  onClick,
  children,
}: {
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <Anchor
      onClick={(event) => {
        event.stopPropagation();
        onClick();
      }}
      underline="hover"
    >
      {children}
    </Anchor>
  );
}

function DateField({ log }: { log: Log }) {
  return <Text>{humanizeDate(log.savedAt)}</Text>;
}

function ActorField({
  log,
  onTableFilterChange,
}: {
  log: Log;
  onTableFilterChange: (name: string, value: string) => void;
}) {
  return (
    log.actor && (
      <InlineFilterLink
        onClick={() => onTableFilterChange("actorRef", log.actor!.ref)}
      >
        {log.actor.name}
      </InlineFilterLink>
    )
  );
}

function ActionTypeField({
  log,
  onTableFilterChange,
}: {
  log: Log;
  onTableFilterChange: (name: string, value: string) => void;
}) {
  return (
    <InlineFilterLink
      onClick={() => onTableFilterChange("actionType", log.action.type)}
    >
      {labelize(log.action.type)}
    </InlineFilterLink>
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
    <InlineFilterLink
      onClick={() => onTableFilterChange("actionCategory", log.action.category)}
    >
      {labelize(log.action.category)}
    </InlineFilterLink>
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
    <InlineFilterLink
      onClick={() => onTableFilterChange("resourceRef", log.resource!.ref)}
    >
      {log.resource.name}
    </InlineFilterLink>
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
    <InlineFilterLink
      onClick={() => onTableFilterChange("resourceType", log.resource!.type)}
    >
      {labelize(log.resource.type)}
    </InlineFilterLink>
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
      <InlineFilterLink
        key={node.ref}
        onClick={() => onTableFilterChange("nodeRef", node.ref)}
      >
        {node.name}
      </InlineFilterLink>
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
  const location = useLocation();
  const navigate = useNavigate();
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
          onRowClick={({ record }) =>
            navigate(addQueryParamToLocation(location, "log", record.id))
          }
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
