import { Anchor, Stack, Text } from "@mantine/core";
import { IconColumns3 } from "@tabler/icons-react";
import { DataTable, DataTableColumn } from "mantine-datatable";
import { useState } from "react";
import { useLocation, useNavigate, useSearchParams } from "react-router-dom";

import { humanizeDate } from "@/utils/date";
import { labelize, titlize } from "@/utils/format";
import { addQueryParamToLocation } from "@/utils/router";

import { CustomField, Log } from "../api";
import { LogDetails } from "./LogDetails";
import { LogFieldSelector } from "./LogFieldSelector";

export type TableFilterChangeHandler = (
  name: string,
  value: string | Map<string, string>,
) => void;

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

function getCustomFieldValue(
  fields: CustomField[],
  fieldName: string,
): string | null {
  const field = fields.find((f) => f.name === fieldName);
  return field ? field.value : null;
}

function DateField({ log }: { log: Log }) {
  return <Text>{humanizeDate(log.savedAt)}</Text>;
}

function SourceField({
  log,
  fieldName,
  onTableFilterChange,
}: {
  log: Log;
  fieldName: string;
  onTableFilterChange: TableFilterChangeHandler;
}) {
  if (!log.source) {
    return null;
  }
  const fieldValue = getCustomFieldValue(log.source, fieldName);
  if (!fieldValue) {
    return null;
  }

  return (
    <InlineFilterLink
      onClick={() =>
        onTableFilterChange("source", new Map([[fieldName, fieldValue]]))
      }
    >
      {fieldValue}
    </InlineFilterLink>
  );
}

function ActorField({
  log,
  onTableFilterChange,
}: {
  log: Log;
  onTableFilterChange: TableFilterChangeHandler;
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

function ActorTypeField({
  log,
  onTableFilterChange,
}: {
  log: Log;
  onTableFilterChange: TableFilterChangeHandler;
}) {
  return (
    log.actor && (
      <InlineFilterLink
        onClick={() => onTableFilterChange("actorType", log.actor!.type)}
      >
        {titlize(log.actor.type)}
      </InlineFilterLink>
    )
  );
}

function ActorNameField({
  log,
  onTableFilterChange,
}: {
  log: Log;
  onTableFilterChange: TableFilterChangeHandler;
}) {
  return (
    log.actor && (
      <InlineFilterLink
        onClick={() => onTableFilterChange("actorName", log.actor!.name)}
      >
        {log.actor.name}
      </InlineFilterLink>
    )
  );
}

function ActorRefField({
  log,
  onTableFilterChange,
}: {
  log: Log;
  onTableFilterChange: TableFilterChangeHandler;
}) {
  return (
    log.actor && (
      <InlineFilterLink
        onClick={() => onTableFilterChange("actorRef", log.actor!.ref)}
      >
        {log.actor.ref}
      </InlineFilterLink>
    )
  );
}

function ActorCustomField({
  log,
  fieldName,
  onTableFilterChange,
}: {
  log: Log;
  fieldName: string;
  onTableFilterChange: TableFilterChangeHandler;
}) {
  if (!log.actor) {
    return null;
  }
  const fieldValue = getCustomFieldValue(log.actor.extra, fieldName);
  if (!fieldValue) {
    return null;
  }

  return (
    <InlineFilterLink
      onClick={() =>
        onTableFilterChange("actorExtra", new Map([[fieldName, fieldValue]]))
      }
    >
      {fieldValue}
    </InlineFilterLink>
  );
}

function ActionTypeField({
  log,
  onTableFilterChange,
}: {
  log: Log;
  onTableFilterChange: TableFilterChangeHandler;
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
  onTableFilterChange: TableFilterChangeHandler;
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
  onTableFilterChange: TableFilterChangeHandler;
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
  onTableFilterChange: TableFilterChangeHandler;
}) {
  return log.resource ? (
    <InlineFilterLink
      onClick={() => onTableFilterChange("resourceType", log.resource!.type)}
    >
      {titlize(log.resource.type)}
    </InlineFilterLink>
  ) : null;
}

function ResourceNameField({
  log,
  onTableFilterChange,
}: {
  log: Log;
  onTableFilterChange: TableFilterChangeHandler;
}) {
  return log.resource ? (
    <InlineFilterLink
      onClick={() => onTableFilterChange("resourceName", log.resource!.name)}
    >
      {log.resource.name}
    </InlineFilterLink>
  ) : null;
}

function ResourceRefField({
  log,
  onTableFilterChange,
}: {
  log: Log;
  onTableFilterChange: TableFilterChangeHandler;
}) {
  return log.resource ? (
    <InlineFilterLink
      onClick={() => onTableFilterChange("resourceRef", log.resource!.ref)}
    >
      {log.resource.ref}
    </InlineFilterLink>
  ) : null;
}

function ResourceCustomField({
  log,
  fieldName,
  onTableFilterChange,
}: {
  log: Log;
  fieldName: string;
  onTableFilterChange: TableFilterChangeHandler;
}) {
  if (!log.resource) {
    return null;
  }
  const fieldValue = getCustomFieldValue(log.resource.extra, fieldName);
  if (!fieldValue) {
    return null;
  }

  return (
    <InlineFilterLink
      onClick={() =>
        onTableFilterChange("resourceExtra", new Map([[fieldName, fieldValue]]))
      }
    >
      {fieldValue}
    </InlineFilterLink>
  );
}

function DetailField({
  log,
  fieldName,
  onTableFilterChange,
}: {
  log: Log;
  fieldName: string;
  onTableFilterChange: TableFilterChangeHandler;
}) {
  if (!log.details) {
    return null;
  }
  const fieldValue = getCustomFieldValue(log.details, fieldName);
  if (!fieldValue) {
    return null;
  }

  return (
    <InlineFilterLink
      onClick={() =>
        onTableFilterChange("details", new Map([[fieldName, fieldValue]]))
      }
    >
      {fieldValue}
    </InlineFilterLink>
  );
}

function NodePathField({
  log,
  onTableFilterChange,
}: {
  log: Log;
  onTableFilterChange: TableFilterChangeHandler;
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

function sortFields(a: string, b: string) {
  const order: { [key: string]: number } = {
    date: 0,
    "source.": 1,
    actor: 2,
    actorType: 3,
    actorName: 4,
    actorRef: 5,
    "actor.": 6,
    actionType: 7,
    actionCategory: 8,
    resource: 9,
    resourceType: 10,
    resourceName: 11,
    resourceRef: 12,
    "resource.": 13,
    "details.": 14,
    node: 15,
  };
  const splitFieldName = (name: string) => {
    const parts = name.split(".");
    return [parts[0] + (parts[1] ? "." : ""), parts[1]];
  };

  const [mainA, customA] = splitFieldName(a);
  const [mainB, customB] = splitFieldName(b);
  const ret = order[mainA] - order[mainB];
  if (ret !== 0) {
    return ret;
  }

  return customA.localeCompare(customB);
}

function fieldToColumn(
  field: string,
  onTableFilterChange: TableFilterChangeHandler,
) {
  if (field === "date")
    return {
      accessor: "savedAt",
      title: "Date",
      render: (log: Log) => <DateField log={log} />,
    };

  if (field.startsWith("source.")) {
    const fieldName = field.split(".")[1];
    return {
      accessor: `source.${fieldName}`,
      title: "Source: " + labelize(fieldName),
      render: (log: Log) => (
        <SourceField
          log={log}
          fieldName={fieldName}
          onTableFilterChange={onTableFilterChange}
        />
      ),
    };
  }

  if (field === "actor")
    return {
      accessor: "actor",
      title: "Actor",
      render: (log: Log) => (
        <ActorField log={log} onTableFilterChange={onTableFilterChange} />
      ),
    };

  if (field === "actorType")
    return {
      accessor: "actorType",
      title: "Actor type",
      render: (log: Log) => (
        <ActorTypeField log={log} onTableFilterChange={onTableFilterChange} />
      ),
    };

  if (field === "actorName")
    return {
      accessor: "actorName",
      title: "Actor name",
      render: (log: Log) => (
        <ActorNameField log={log} onTableFilterChange={onTableFilterChange} />
      ),
    };

  if (field === "actorRef")
    return {
      accessor: "actorRef",
      title: "Actor ref",
      render: (log: Log) => (
        <ActorRefField log={log} onTableFilterChange={onTableFilterChange} />
      ),
    };

  if (field.startsWith("actor.")) {
    const fieldName = field.split(".")[1];
    return {
      accessor: `actor.${fieldName}`,
      title: "Actor " + labelize(fieldName),
      render: (log: Log) => (
        <ActorCustomField
          log={log}
          fieldName={fieldName}
          onTableFilterChange={onTableFilterChange}
        />
      ),
    };
  }

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

  if (field === "resourceName")
    return {
      accessor: "resourceName",
      title: "Resource name",
      render: (log: Log) => (
        <ResourceNameField
          log={log}
          onTableFilterChange={onTableFilterChange}
        />
      ),
    };

  if (field === "resourceRef")
    return {
      accessor: "resourceRef",
      title: "Resource ref",
      render: (log: Log) => (
        <ResourceRefField log={log} onTableFilterChange={onTableFilterChange} />
      ),
    };

  if (field.startsWith("resource.")) {
    const fieldName = field.split(".")[1];
    return {
      accessor: `resource.${fieldName}`,
      title: "Resource " + labelize(fieldName),
      render: (log: Log) => (
        <ResourceCustomField
          log={log}
          fieldName={fieldName}
          onTableFilterChange={onTableFilterChange}
        />
      ),
    };
  }

  if (field.startsWith("details.")) {
    const fieldName = field.split(".")[1];
    return {
      accessor: `details.${fieldName}`,
      title: titlize(fieldName),
      render: (log: Log) => (
        <DetailField
          log={log}
          fieldName={fieldName}
          onTableFilterChange={onTableFilterChange}
        />
      ),
    };
  }

  if (field === "node")
    return {
      accessor: "node",
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
  onTableFilterChange: TableFilterChangeHandler;
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
      "node",
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
      .toSorted(sortFields)
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
