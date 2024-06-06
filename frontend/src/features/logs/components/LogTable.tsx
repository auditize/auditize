import { Anchor, Stack, Text } from "@mantine/core";
import { IconColumns3 } from "@tabler/icons-react";
import { DataTable, DataTableColumn } from "mantine-datatable";
import { useState } from "react";
import { useLocation, useNavigate, useSearchParams } from "react-router-dom";

import { humanizeDate } from "@/utils/date";
import { titlize } from "@/utils/format";
import { addQueryParamToLocation } from "@/utils/router";

import { Log } from "../api";
import { LogDetails } from "./LogDetails";
import { LogFieldSelector } from "./LogFieldSelector";

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
      {titlize(log.action.type)}
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
      {titlize(log.action.category)}
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
      {titlize(log.resource.type)}
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

function ColumnSelector({
  repoId,
  selected,
  onColumnAdded,
  onColumnRemoved,
}: {
  repoId: string;
  selected: Set<string>;
  onColumnAdded: (name: string) => void;
  onColumnRemoved: (name: string) => void;
}) {
  return (
    <LogFieldSelector
      repoId={repoId}
      selected={selected}
      onSelected={onColumnAdded}
      onUnselected={onColumnRemoved}
      enableCompositeFields
    >
      <IconColumns3 />
    </LogFieldSelector>
  );
}

function fieldToColumn(
  field: string,
  onTableFilterChange: (name: string, value: string) => void,
) {
  if (field === "date")
    return {
      accessor: "savedAt",
      title: "Date",
      render: (log: Log) => <DateField log={log} />,
    };

  if (field === "actor")
    return {
      accessor: "actorRef",
      title: "Actor",
      render: (log: Log) => (
        <ActorField log={log} onTableFilterChange={onTableFilterChange} />
      ),
    };

  if (field === "actionType")
    return {
      accessor: "actionType",
      title: "Action type",
      render: (log: Log) => (
        <ActionTypeField log={log} onTableFilterChange={onTableFilterChange} />
      ),
    };

  if (field === "actionCategory")
    return {
      accessor: "actionCategory",
      title: "Action category",
      render: (log: Log) => (
        <ActionCategoryField
          log={log}
          onTableFilterChange={onTableFilterChange}
        />
      ),
    };

  if (field === "resource")
    return {
      accessor: "resource",
      title: "Resource",
      render: (log: Log) => (
        <ResourceField log={log} onTableFilterChange={onTableFilterChange} />
      ),
    };

  if (field === "resourceType")
    return {
      accessor: "resourceType",
      title: "Resource type",
      render: (log: Log) => (
        <ResourceTypeField
          log={log}
          onTableFilterChange={onTableFilterChange}
        />
      ),
    };

  if (field === "nodePath")
    return {
      accessor: "nodePath",
      title: "Node",
      render: (log: Log) => (
        <NodePathField log={log} onTableFilterChange={onTableFilterChange} />
      ),
    };

  console.error(`Unknown field: ${field}`);
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
  const [selectedColumns, setSelectedColumns] = useState<Set<string>>(
    new Set([
      "date",
      "actor",
      "actionType",
      "actionCategory",
      "resource",
      "resourceType",
      "nodePath",
    ]),
  );
  const addColumn = (name: string) => {
    setSelectedColumns(new Set([...selectedColumns, name]));
  };
  const removeColumn = (name: string) => {
    setSelectedColumns(new Set([...selectedColumns].filter((n) => n !== name)));
  };

  let columns = [
    ...Array.from(selectedColumns)
      .map((column) => fieldToColumn(column, onTableFilterChange))
      .filter((data) => !!data),
    {
      accessor: "columns",
      title: (
        // Disable the inherited bold font style
        <span style={{ fontWeight: "normal" }}>
          <ColumnSelector
            repoId={repoId}
            selected={selectedColumns}
            onColumnAdded={addColumn}
            onColumnRemoved={removeColumn}
          />
        </span>
      ),
    },
  ];

  return (
    <>
      <Stack>
        <DataTable
          columns={columns as DataTableColumn<Log>[]}
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
