import {
  ActionIcon,
  Anchor,
  Badge,
  Breadcrumbs,
  Stack,
  Text,
  useCombobox,
} from "@mantine/core";
import { useLocalStorage } from "@mantine/hooks";
import { IconColumns3 } from "@tabler/icons-react";
import i18n from "i18next";
import { DataTable, DataTableColumn } from "mantine-datatable";
import { useTranslation } from "react-i18next";
import { useLocation, useNavigate, useSearchParams } from "react-router-dom";

import { CustomMultiSelect } from "@/components/CustomMultiSelect";
import { humanizeDate } from "@/utils/date";
import { addQueryParamToLocation } from "@/utils/router";

import { CustomField, Log } from "../api";
import { useLogContext } from "../context";
import { LogDetails } from "./LogDetails";
import { useLogFields } from "./LogFieldSelector";
import { useLogTranslator } from "./LogTranslation";

export type TableFilterChangeHandler = (
  name: string,
  value: string | Map<string, string>,
) => void;

function InlineFilterLink({
  onClick,
  fontSize = "sm",
  fontWeight,
  color,
  children,
}: {
  onClick: () => void;
  fontSize?: string;
  fontWeight?: string | number;
  color?: string;
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
      <Text component="span" size={fontSize} fw={fontWeight} c={color}>
        {children}
      </Text>
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
  return <Text size="sm">{humanizeDate(log.savedAt)}</Text>;
}

function SourceField({
  log,
  fieldName,
  repoId,
  onTableFilterChange,
}: {
  log: Log;
  fieldName: string;
  repoId: string;
  onTableFilterChange: TableFilterChangeHandler;
}) {
  const logTranslator = useLogTranslator(repoId);

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
      {logTranslator("source_field", fieldValue)}
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
  repoId,
  onTableFilterChange,
}: {
  log: Log;
  repoId: string;
  onTableFilterChange: TableFilterChangeHandler;
}) {
  const logTranslator = useLogTranslator(repoId);

  return (
    log.actor && (
      <InlineFilterLink
        onClick={() => onTableFilterChange("actorType", log.actor!.type)}
      >
        {logTranslator("actor_type", log.actor.type)}
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

function ActionField({
  log,
  repoId,
  onTableFilterChange,
}: {
  log: Log;
  repoId: string;
  onTableFilterChange: TableFilterChangeHandler;
}) {
  const logTranslator = useLogTranslator(repoId);

  return (
    <>
      <InlineFilterLink
        onClick={() => onTableFilterChange("actionType", log.action.type)}
      >
        {logTranslator("action_type", log.action.type)}
      </InlineFilterLink>
      <br />
      <InlineFilterLink
        onClick={() =>
          onTableFilterChange("actionCategory", log.action.category)
        }
        color="gray"
        fontSize="xs"
      >
        {"(" + logTranslator("action_category", log.action.category) + ")"}
      </InlineFilterLink>
    </>
  );
}

function ActionTypeField({
  log,
  repoId,
  onTableFilterChange,
}: {
  log: Log;
  repoId: string;
  onTableFilterChange: TableFilterChangeHandler;
}) {
  const logTranslator = useLogTranslator(repoId);

  return (
    <InlineFilterLink
      onClick={() => onTableFilterChange("actionType", log.action.type)}
    >
      {logTranslator("action_type", log.action.type)}
    </InlineFilterLink>
  );
}

function ActionCategoryField({
  log,
  repoId,
  onTableFilterChange,
}: {
  log: Log;
  repoId: string;
  onTableFilterChange: TableFilterChangeHandler;
}) {
  const logTranslator = useLogTranslator(repoId);

  return (
    <InlineFilterLink
      onClick={() => onTableFilterChange("actionCategory", log.action.category)}
    >
      {logTranslator("action_category", log.action.category)}
    </InlineFilterLink>
  );
}

function ResourceField({
  log,
  repoId,
  onTableFilterChange,
}: {
  log: Log;
  repoId: string;
  onTableFilterChange: TableFilterChangeHandler;
}) {
  const logTranslator = useLogTranslator(repoId);

  return log.resource ? (
    <>
      <InlineFilterLink
        onClick={() => onTableFilterChange("resourceType", log.resource!.type)}
      >
        {logTranslator("resource_type", log.resource.type)}
      </InlineFilterLink>
      {": "}
      <InlineFilterLink
        onClick={() => onTableFilterChange("resourceRef", log.resource!.ref)}
        fontWeight="bold"
      >
        {log.resource.name}
      </InlineFilterLink>
    </>
  ) : null;
}

function ResourceTypeField({
  log,
  repoId,
  onTableFilterChange,
}: {
  log: Log;
  repoId: string;
  onTableFilterChange: TableFilterChangeHandler;
}) {
  const logTranslator = useLogTranslator(repoId);

  return log.resource ? (
    <InlineFilterLink
      onClick={() => onTableFilterChange("resourceType", log.resource!.type)}
    >
      {logTranslator("resource_type", log.resource.type)}
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

function TagsField({
  log,
  repoId,
  onTableFilterChange,
}: {
  log: Log;
  repoId: string;
  onTableFilterChange: TableFilterChangeHandler;
}) {
  const logTranslator = useLogTranslator(repoId);

  return (
    <Breadcrumbs separator={null} separatorMargin="0.250rem">
      {log.tags.map((tag, i) =>
        tag.ref ? (
          <InlineFilterLink
            key={i}
            onClick={() => onTableFilterChange("tagRef", tag.ref!)}
          >
            <Badge size="sm" variant="outline">
              {logTranslator("tag_type", tag.type) + ": " + tag.name}
            </Badge>
          </InlineFilterLink>
        ) : (
          <InlineFilterLink
            key={i}
            onClick={() => onTableFilterChange("tagType", tag.type)}
          >
            <Badge size="sm" variant="outline">
              {logTranslator("tag_type", tag.type)}
            </Badge>
          </InlineFilterLink>
        ),
      )}
    </Breadcrumbs>
  );
}

function TagTypesField({
  log,
  repoId,
  onTableFilterChange,
}: {
  log: Log;
  repoId: string;
  onTableFilterChange: TableFilterChangeHandler;
}) {
  const logTranslator = useLogTranslator(repoId);

  return (
    <Breadcrumbs separator=", ">
      {log.tags.map((tag, i) => (
        <InlineFilterLink
          key={i}
          onClick={() => onTableFilterChange("tagType", tag.type)}
        >
          {logTranslator("tag_type", tag.type)}
        </InlineFilterLink>
      ))}
    </Breadcrumbs>
  );
}

function TagNamesField({
  log,
  onTableFilterChange,
}: {
  log: Log;
  onTableFilterChange: TableFilterChangeHandler;
}) {
  return (
    <Breadcrumbs separator=", ">
      {log.tags.map(
        (tag, i) =>
          tag.name && (
            <InlineFilterLink
              key={i}
              onClick={() => onTableFilterChange("tagName", tag.name!)}
            >
              {tag.name}
            </InlineFilterLink>
          ),
      )}
    </Breadcrumbs>
  );
}

function TagRefsField({
  log,
  onTableFilterChange,
}: {
  log: Log;
  onTableFilterChange: TableFilterChangeHandler;
}) {
  return (
    <Breadcrumbs separator=", ">
      {log.tags.map(
        (tag, i) =>
          tag.ref && (
            <InlineFilterLink
              key={i}
              onClick={() => onTableFilterChange("tagRef", tag.ref!)}
            >
              {tag.ref}
            </InlineFilterLink>
          ),
      )}
    </Breadcrumbs>
  );
}

function AttachmentNamesField({
  log,
  onTableFilterChange,
}: {
  log: Log;
  onTableFilterChange: TableFilterChangeHandler;
}) {
  return (
    <Breadcrumbs separator=", ">
      {log.attachments.map((attachment, i) => (
        <InlineFilterLink
          key={i}
          onClick={() => onTableFilterChange("attachmentName", attachment.name)}
        >
          {attachment.name}
        </InlineFilterLink>
      ))}
    </Breadcrumbs>
  );
}

function AttachmentDescriptionsField({
  log,
  onTableFilterChange,
}: {
  log: Log;
  onTableFilterChange: TableFilterChangeHandler;
}) {
  return (
    <Breadcrumbs separator=", ">
      {log.attachments.map((attachment, i) => (
        <InlineFilterLink
          key={i}
          onClick={() =>
            onTableFilterChange("attachmentDescription", attachment.description)
          }
        >
          {attachment.description}
        </InlineFilterLink>
      ))}
    </Breadcrumbs>
  );
}

function AttachmentTypesField({
  log,
  repoId,
  onTableFilterChange,
}: {
  log: Log;
  repoId: string;
  onTableFilterChange: TableFilterChangeHandler;
}) {
  const logTranslator = useLogTranslator(repoId);

  return (
    <Breadcrumbs separator=", ">
      {log.attachments.map((attachment, i) => (
        <InlineFilterLink
          key={i}
          onClick={() => onTableFilterChange("attachmentType", attachment.type)}
        >
          {logTranslator("attachment_type", attachment.type)}
        </InlineFilterLink>
      ))}
    </Breadcrumbs>
  );
}

function AttachmentMimeTypesField({
  log,
  onTableFilterChange,
}: {
  log: Log;
  onTableFilterChange: TableFilterChangeHandler;
}) {
  return (
    <Breadcrumbs separator=", ">
      {log.attachments.map((attachment, i) => (
        <InlineFilterLink
          key={i}
          onClick={() =>
            onTableFilterChange("attachmentMimeType", attachment.mimeType)
          }
        >
          {attachment.mimeType}
        </InlineFilterLink>
      ))}
    </Breadcrumbs>
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
  onColumnReset,
}: {
  repoId: string;
  selected: Array<string>;
  onColumnAdded: (name: string) => void;
  onColumnRemoved: (name: string) => void;
  onColumnReset: () => void;
}) {
  const { t } = useTranslation();
  const { fields, loading: fieldsLoading } = useLogFields(
    repoId,
    undefined,
    true,
  );
  const comboboxStore = useCombobox();

  return (
    <CustomMultiSelect
      comboboxStore={comboboxStore}
      data={fields}
      value={Array.from(selected)}
      onOptionSubmit={onColumnAdded}
      onRemove={onColumnRemoved}
      footer={
        <Anchor onClick={onColumnReset}>
          <Text size="xs">{t("log.list.columnSelector.reset")}</Text>
        </Anchor>
      }
    >
      <ActionIcon
        onClick={() => comboboxStore.toggleDropdown()}
        loading={fieldsLoading}
        loaderProps={{ type: "dots" }}
        variant="transparent"
      >
        <IconColumns3 />
      </ActionIcon>
    </CustomMultiSelect>
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
    action: 7,
    actionType: 8,
    actionCategory: 9,
    resource: 10,
    resourceType: 11,
    resourceName: 12,
    resourceRef: 13,
    "resource.": 14,
    "details.": 15,
    attachment: 16,
    atachmentName: 17,
    attachmentDescription: 18,
    attachmentType: 19,
    attachmentMimeType: 20,
    node: 21,
    tag: 22,
    tagType: 23,
    tagName: 24,
    tagRef: 25,
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
  repoId: string,
  onTableFilterChange: TableFilterChangeHandler,
  logTranslator: (type: string, key: string) => string,
) {
  const { t } = i18n;

  if (field === "date")
    return {
      accessor: "savedAt",
      title: t("log.date"),
      render: (log: Log) => <DateField log={log} />,
    };

  if (field.startsWith("source.")) {
    const fieldName = field.split(".")[1];
    return {
      accessor: `source.${fieldName}`,
      title: t("log.source") + ": " + logTranslator("source_field", fieldName),
      render: (log: Log) => (
        <SourceField
          log={log}
          fieldName={fieldName}
          repoId={repoId}
          onTableFilterChange={onTableFilterChange}
        />
      ),
    };
  }

  if (field === "actor")
    return {
      accessor: "actor",
      title: t("log.actor"),
      render: (log: Log) => (
        <ActorField log={log} onTableFilterChange={onTableFilterChange} />
      ),
    };

  if (field === "actorType")
    return {
      accessor: "actorType",
      title: t("log.actorType"),
      render: (log: Log) => (
        <ActorTypeField
          log={log}
          repoId={repoId}
          onTableFilterChange={onTableFilterChange}
        />
      ),
    };

  if (field === "actorName")
    return {
      accessor: "actorName",
      title: t("log.actorName"),
      render: (log: Log) => (
        <ActorNameField log={log} onTableFilterChange={onTableFilterChange} />
      ),
    };

  if (field === "actorRef")
    return {
      accessor: "actorRef",
      title: t("log.actorRef"),
      render: (log: Log) => (
        <ActorRefField log={log} onTableFilterChange={onTableFilterChange} />
      ),
    };

  if (field.startsWith("actor.")) {
    const fieldName = field.split(".")[1];
    return {
      accessor: `actor.${fieldName}`,
      title:
        t("log.actor") + ": " + logTranslator("actor_custom_field", fieldName),
      render: (log: Log) => (
        <ActorCustomField
          log={log}
          fieldName={fieldName}
          onTableFilterChange={onTableFilterChange}
        />
      ),
    };
  }

  if (field === "action")
    return {
      accessor: "action",
      title: t("log.action"),
      render: (log: Log) => (
        <ActionField
          log={log}
          repoId={repoId}
          onTableFilterChange={onTableFilterChange}
        />
      ),
    };

  if (field === "actionType")
    return {
      accessor: "actionType",
      title: t("log.actionType"),
      render: (log: Log) => (
        <ActionTypeField
          log={log}
          repoId={repoId}
          onTableFilterChange={onTableFilterChange}
        />
      ),
    };

  if (field === "actionCategory")
    return {
      accessor: "actionCategory",
      title: t("log.actionCategory"),
      render: (log: Log) => (
        <ActionCategoryField
          log={log}
          repoId={repoId}
          onTableFilterChange={onTableFilterChange}
        />
      ),
    };

  if (field === "resource")
    return {
      accessor: "resource",
      title: t("log.resource"),
      render: (log: Log) => (
        <ResourceField
          log={log}
          repoId={repoId}
          onTableFilterChange={onTableFilterChange}
        />
      ),
    };

  if (field === "resourceType")
    return {
      accessor: "resourceType",
      title: t("log.resourceType"),
      render: (log: Log) => (
        <ResourceTypeField
          log={log}
          repoId={repoId}
          onTableFilterChange={onTableFilterChange}
        />
      ),
    };

  if (field === "resourceName")
    return {
      accessor: "resourceName",
      title: t("log.resourceName"),
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
      title: t("log.resourceRef"),
      render: (log: Log) => (
        <ResourceRefField log={log} onTableFilterChange={onTableFilterChange} />
      ),
    };

  if (field.startsWith("resource.")) {
    const fieldName = field.split(".")[1];
    return {
      accessor: `resource.${fieldName}`,
      title:
        t("log.resource") +
        ": " +
        logTranslator("resource_custom_field", fieldName),
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
      title: logTranslator("detail_field", fieldName),
      render: (log: Log) => (
        <DetailField
          log={log}
          fieldName={fieldName}
          onTableFilterChange={onTableFilterChange}
        />
      ),
    };
  }

  if (field === "tag")
    return {
      accessor: "tags",
      title: t("log.tags"),
      render: (log: Log) => (
        <TagsField
          log={log}
          repoId={repoId}
          onTableFilterChange={onTableFilterChange}
        />
      ),
    };

  if (field === "tagType")
    return {
      accessor: "tagType",
      title: t("log.tagTypes"),
      render: (log: Log) => (
        <TagTypesField
          log={log}
          repoId={repoId}
          onTableFilterChange={onTableFilterChange}
        />
      ),
    };

  if (field === "tagName")
    return {
      accessor: "tagName",
      title: t("log.tagNames"),
      render: (log: Log) => (
        <TagNamesField log={log} onTableFilterChange={onTableFilterChange} />
      ),
    };

  if (field === "tagRef")
    return {
      accessor: "tagRef",
      title: t("log.tagRefs"),
      render: (log: Log) => (
        <TagRefsField log={log} onTableFilterChange={onTableFilterChange} />
      ),
    };

  if (field === "attachment")
    return {
      accessor: "attachment",
      title: t("log.attachments"),
      // NB: display attachments like attachment types for now
      render: (log: Log) => (
        <AttachmentTypesField
          log={log}
          repoId={repoId}
          onTableFilterChange={onTableFilterChange}
        />
      ),
    };

  if (field === "attachmentName")
    return {
      accessor: "attachmentName",
      title: t("log.attachmentNames"),
      render: (log: Log) => (
        <AttachmentNamesField
          log={log}
          onTableFilterChange={onTableFilterChange}
        />
      ),
    };

  if (field === "attachmentDescription")
    return {
      accessor: "attachmentDescription",
      title: t("log.attachmentDescriptions"),
      render: (log: Log) => (
        <AttachmentDescriptionsField
          log={log}
          onTableFilterChange={onTableFilterChange}
        />
      ),
    };

  if (field === "attachmentType")
    return {
      accessor: "attachmentType",
      title: t("log.attachmentTypes"),
      render: (log: Log) => (
        <AttachmentTypesField
          log={log}
          repoId={repoId}
          onTableFilterChange={onTableFilterChange}
        />
      ),
    };

  if (field === "attachmentMimeType")
    return {
      accessor: "attachmentMimeType",
      title: t("log.attachmentMimeTypes"),
      render: (log: Log) => (
        <AttachmentMimeTypesField
          log={log}
          onTableFilterChange={onTableFilterChange}
        />
      ),
    };

  if (field === "node")
    return {
      accessor: "node",
      title: t("log.node"),
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
  const defaultColumns = ["date", "actor", "action", "resource", "node", "tag"];
  const { setDisplayedLogId } = useLogContext();
  const [selectedColumns, setSelectedColumns] = useLocalStorage<
    Record<string, string[]>
  >({
    key: `log-columns`,
    defaultValue: {},
  });
  const logTranslator = useLogTranslator(repoId);
  const addColumn = (name: string) => {
    setSelectedColumns((selectedColumns) => ({
      ...selectedColumns,
      [repoId]: [...(selectedColumns[repoId] || defaultColumns), name],
    }));
  };
  const removeColumn = (name: string) => {
    setSelectedColumns((selectedColumns) => ({
      ...selectedColumns,
      [repoId]: [...(selectedColumns[repoId] || defaultColumns)].filter(
        (n) => n !== name,
      ),
    }));
  };
  const resetColumns = () => {
    setSelectedColumns((selectedColumns) => ({
      ...selectedColumns,
      [repoId]: defaultColumns,
    }));
  };

  let columns = [
    ...(selectedColumns[repoId] || defaultColumns)
      .toSorted(sortFields)
      .map((column) =>
        fieldToColumn(column, repoId, onTableFilterChange, logTranslator),
      )
      .filter((data) => !!data),
    {
      accessor: "columns",
      title: (
        // Disable the inherited bold font style
        <span style={{ fontWeight: "normal" }}>
          <ColumnSelector
            repoId={repoId}
            selected={selectedColumns[repoId] || defaultColumns}
            onColumnAdded={addColumn}
            onColumnRemoved={removeColumn}
            onColumnReset={resetColumns}
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
          onRowClick={({ record }) => setDisplayedLogId(record.id)}
          fetching={isLoading}
          minHeight={150}
          noRecordsText="No logs found"
        />
        {logs && logs.length > 0 && footer}
      </Stack>
      <LogDetails repoId={repoId} />
    </>
  );
}
