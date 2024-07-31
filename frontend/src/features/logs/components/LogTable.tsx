import {
  ActionIcon,
  Anchor,
  Badge,
  Breadcrumbs,
  Button,
  Center,
  Stack,
  Text,
  useCombobox,
} from "@mantine/core";
import { IconColumns3 } from "@tabler/icons-react";
import { useInfiniteQuery } from "@tanstack/react-query";
import i18n from "i18next";
import { DataTable, DataTableColumn } from "mantine-datatable";
import { useTranslation } from "react-i18next";

import { CustomMultiSelect } from "@/components/CustomMultiSelect";
import { humanizeDate } from "@/utils/date";

import { CustomField, getLogs, Log } from "../api";
import { LogSearchParams } from "../LogSearchParams";
import { LogDetails } from "./LogDetails";
import { useLogFields } from "./LogFieldSelector";
import { useLogNavigationState } from "./LogNavigationState";
import { useLogTranslator } from "./LogTranslation";

export type TableSearchParamChangeHandler = (
  name: string,
  value: string | Map<string, string>,
) => void;

function InlineSearchParamLink({
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
  onTableSearchParamChange,
}: {
  log: Log;
  fieldName: string;
  repoId: string;
  onTableSearchParamChange: TableSearchParamChangeHandler;
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
    <InlineSearchParamLink
      onClick={() =>
        onTableSearchParamChange("source", new Map([[fieldName, fieldValue]]))
      }
    >
      {logTranslator("source_field", fieldValue)}
    </InlineSearchParamLink>
  );
}

function ActorField({
  log,
  onTableSearchParamChange,
}: {
  log: Log;
  onTableSearchParamChange: TableSearchParamChangeHandler;
}) {
  return (
    log.actor && (
      <InlineSearchParamLink
        onClick={() => onTableSearchParamChange("actorRef", log.actor!.ref)}
      >
        {log.actor.name}
      </InlineSearchParamLink>
    )
  );
}

function ActorTypeField({
  log,
  repoId,
  onTableSearchParamChange,
}: {
  log: Log;
  repoId: string;
  onTableSearchParamChange: TableSearchParamChangeHandler;
}) {
  const logTranslator = useLogTranslator(repoId);

  return (
    log.actor && (
      <InlineSearchParamLink
        onClick={() => onTableSearchParamChange("actorType", log.actor!.type)}
      >
        {logTranslator("actor_type", log.actor.type)}
      </InlineSearchParamLink>
    )
  );
}

function ActorNameField({
  log,
  onTableSearchParamChange,
}: {
  log: Log;
  onTableSearchParamChange: TableSearchParamChangeHandler;
}) {
  return (
    log.actor && (
      <InlineSearchParamLink
        onClick={() => onTableSearchParamChange("actorName", log.actor!.name)}
      >
        {log.actor.name}
      </InlineSearchParamLink>
    )
  );
}

function ActorRefField({
  log,
  onTableSearchParamChange,
}: {
  log: Log;
  onTableSearchParamChange: TableSearchParamChangeHandler;
}) {
  return (
    log.actor && (
      <InlineSearchParamLink
        onClick={() => onTableSearchParamChange("actorRef", log.actor!.ref)}
      >
        {log.actor.ref}
      </InlineSearchParamLink>
    )
  );
}

function ActorCustomField({
  log,
  fieldName,
  onTableSearchParamChange,
}: {
  log: Log;
  fieldName: string;
  onTableSearchParamChange: TableSearchParamChangeHandler;
}) {
  if (!log.actor) {
    return null;
  }
  const fieldValue = getCustomFieldValue(log.actor.extra, fieldName);
  if (!fieldValue) {
    return null;
  }

  return (
    <InlineSearchParamLink
      onClick={() =>
        onTableSearchParamChange(
          "actorExtra",
          new Map([[fieldName, fieldValue]]),
        )
      }
    >
      {fieldValue}
    </InlineSearchParamLink>
  );
}

function ActionField({
  log,
  repoId,
  onTableSearchParamChange,
}: {
  log: Log;
  repoId: string;
  onTableSearchParamChange: TableSearchParamChangeHandler;
}) {
  const logTranslator = useLogTranslator(repoId);

  return (
    <>
      <InlineSearchParamLink
        onClick={() => onTableSearchParamChange("actionType", log.action.type)}
      >
        {logTranslator("action_type", log.action.type)}
      </InlineSearchParamLink>
      <br />
      <InlineSearchParamLink
        onClick={() =>
          onTableSearchParamChange("actionCategory", log.action.category)
        }
        color="gray"
        fontSize="xs"
      >
        {"(" + logTranslator("action_category", log.action.category) + ")"}
      </InlineSearchParamLink>
    </>
  );
}

function ActionTypeField({
  log,
  repoId,
  onTableSearchParamChange,
}: {
  log: Log;
  repoId: string;
  onTableSearchParamChange: TableSearchParamChangeHandler;
}) {
  const logTranslator = useLogTranslator(repoId);

  return (
    <InlineSearchParamLink
      onClick={() => onTableSearchParamChange("actionType", log.action.type)}
    >
      {logTranslator("action_type", log.action.type)}
    </InlineSearchParamLink>
  );
}

function ActionCategoryField({
  log,
  repoId,
  onTableSearchParamChange,
}: {
  log: Log;
  repoId: string;
  onTableSearchParamChange: TableSearchParamChangeHandler;
}) {
  const logTranslator = useLogTranslator(repoId);

  return (
    <InlineSearchParamLink
      onClick={() =>
        onTableSearchParamChange("actionCategory", log.action.category)
      }
    >
      {logTranslator("action_category", log.action.category)}
    </InlineSearchParamLink>
  );
}

function ResourceField({
  log,
  repoId,
  onTableSearchParamChange,
}: {
  log: Log;
  repoId: string;
  onTableSearchParamChange: TableSearchParamChangeHandler;
}) {
  const logTranslator = useLogTranslator(repoId);

  return log.resource ? (
    <>
      <InlineSearchParamLink
        onClick={() =>
          onTableSearchParamChange("resourceType", log.resource!.type)
        }
      >
        {logTranslator("resource_type", log.resource.type)}
      </InlineSearchParamLink>
      {": "}
      <InlineSearchParamLink
        onClick={() =>
          onTableSearchParamChange("resourceRef", log.resource!.ref)
        }
        fontWeight="bold"
      >
        {log.resource.name}
      </InlineSearchParamLink>
    </>
  ) : null;
}

function ResourceTypeField({
  log,
  repoId,
  onTableSearchParamChange,
}: {
  log: Log;
  repoId: string;
  onTableSearchParamChange: TableSearchParamChangeHandler;
}) {
  const logTranslator = useLogTranslator(repoId);

  return log.resource ? (
    <InlineSearchParamLink
      onClick={() =>
        onTableSearchParamChange("resourceType", log.resource!.type)
      }
    >
      {logTranslator("resource_type", log.resource.type)}
    </InlineSearchParamLink>
  ) : null;
}

function ResourceNameField({
  log,
  onTableSearchParamChange,
}: {
  log: Log;
  onTableSearchParamChange: TableSearchParamChangeHandler;
}) {
  return log.resource ? (
    <InlineSearchParamLink
      onClick={() =>
        onTableSearchParamChange("resourceName", log.resource!.name)
      }
    >
      {log.resource.name}
    </InlineSearchParamLink>
  ) : null;
}

function ResourceRefField({
  log,
  onTableSearchParamChange,
}: {
  log: Log;
  onTableSearchParamChange: TableSearchParamChangeHandler;
}) {
  return log.resource ? (
    <InlineSearchParamLink
      onClick={() => onTableSearchParamChange("resourceRef", log.resource!.ref)}
    >
      {log.resource.ref}
    </InlineSearchParamLink>
  ) : null;
}

function ResourceCustomField({
  log,
  fieldName,
  onTableSearchParamChange,
}: {
  log: Log;
  fieldName: string;
  onTableSearchParamChange: TableSearchParamChangeHandler;
}) {
  if (!log.resource) {
    return null;
  }
  const fieldValue = getCustomFieldValue(log.resource.extra, fieldName);
  if (!fieldValue) {
    return null;
  }

  return (
    <InlineSearchParamLink
      onClick={() =>
        onTableSearchParamChange(
          "resourceExtra",
          new Map([[fieldName, fieldValue]]),
        )
      }
    >
      {fieldValue}
    </InlineSearchParamLink>
  );
}

function DetailField({
  log,
  fieldName,
  onTableSearchParamChange,
}: {
  log: Log;
  fieldName: string;
  onTableSearchParamChange: TableSearchParamChangeHandler;
}) {
  if (!log.details) {
    return null;
  }
  const fieldValue = getCustomFieldValue(log.details, fieldName);
  if (!fieldValue) {
    return null;
  }

  return (
    <InlineSearchParamLink
      onClick={() =>
        onTableSearchParamChange("details", new Map([[fieldName, fieldValue]]))
      }
    >
      {fieldValue}
    </InlineSearchParamLink>
  );
}

function TagsField({
  log,
  repoId,
  onTableSearchParamChange,
}: {
  log: Log;
  repoId: string;
  onTableSearchParamChange: TableSearchParamChangeHandler;
}) {
  const logTranslator = useLogTranslator(repoId);

  return (
    <Breadcrumbs separator={null} separatorMargin="0.250rem">
      {log.tags.map((tag, i) =>
        tag.ref ? (
          <InlineSearchParamLink
            key={i}
            onClick={() => onTableSearchParamChange("tagRef", tag.ref!)}
          >
            <Badge size="sm" variant="outline">
              {logTranslator("tag_type", tag.type) + ": " + tag.name}
            </Badge>
          </InlineSearchParamLink>
        ) : (
          <InlineSearchParamLink
            key={i}
            onClick={() => onTableSearchParamChange("tagType", tag.type)}
          >
            <Badge size="sm" variant="outline">
              {logTranslator("tag_type", tag.type)}
            </Badge>
          </InlineSearchParamLink>
        ),
      )}
    </Breadcrumbs>
  );
}

function TagTypesField({
  log,
  repoId,
  onTableSearchParamChange,
}: {
  log: Log;
  repoId: string;
  onTableSearchParamChange: TableSearchParamChangeHandler;
}) {
  const logTranslator = useLogTranslator(repoId);

  return (
    <Breadcrumbs separator=", ">
      {log.tags.map((tag, i) => (
        <InlineSearchParamLink
          key={i}
          onClick={() => onTableSearchParamChange("tagType", tag.type)}
        >
          {logTranslator("tag_type", tag.type)}
        </InlineSearchParamLink>
      ))}
    </Breadcrumbs>
  );
}

function TagNamesField({
  log,
  onTableSearchParamChange,
}: {
  log: Log;
  onTableSearchParamChange: TableSearchParamChangeHandler;
}) {
  return (
    <Breadcrumbs separator=", ">
      {log.tags.map(
        (tag, i) =>
          tag.name && (
            <InlineSearchParamLink
              key={i}
              onClick={() => onTableSearchParamChange("tagName", tag.name!)}
            >
              {tag.name}
            </InlineSearchParamLink>
          ),
      )}
    </Breadcrumbs>
  );
}

function TagRefsField({
  log,
  onTableSearchParamChange,
}: {
  log: Log;
  onTableSearchParamChange: TableSearchParamChangeHandler;
}) {
  return (
    <Breadcrumbs separator=", ">
      {log.tags.map(
        (tag, i) =>
          tag.ref && (
            <InlineSearchParamLink
              key={i}
              onClick={() => onTableSearchParamChange("tagRef", tag.ref!)}
            >
              {tag.ref}
            </InlineSearchParamLink>
          ),
      )}
    </Breadcrumbs>
  );
}

function AttachmentNamesField({
  log,
  onTableSearchParamChange,
}: {
  log: Log;
  onTableSearchParamChange: TableSearchParamChangeHandler;
}) {
  return (
    <Breadcrumbs separator=", ">
      {log.attachments.map((attachment, i) => (
        <InlineSearchParamLink
          key={i}
          onClick={() =>
            onTableSearchParamChange("attachmentName", attachment.name)
          }
        >
          {attachment.name}
        </InlineSearchParamLink>
      ))}
    </Breadcrumbs>
  );
}

function AttachmentTypesField({
  log,
  repoId,
  onTableSearchParamChange,
}: {
  log: Log;
  repoId: string;
  onTableSearchParamChange: TableSearchParamChangeHandler;
}) {
  const logTranslator = useLogTranslator(repoId);

  return (
    <Breadcrumbs separator=", ">
      {log.attachments.map((attachment, i) => (
        <InlineSearchParamLink
          key={i}
          onClick={() =>
            onTableSearchParamChange("attachmentType", attachment.type)
          }
        >
          {logTranslator("attachment_type", attachment.type)}
        </InlineSearchParamLink>
      ))}
    </Breadcrumbs>
  );
}

function AttachmentMimeTypesField({
  log,
  onTableSearchParamChange,
}: {
  log: Log;
  onTableSearchParamChange: TableSearchParamChangeHandler;
}) {
  return (
    <Breadcrumbs separator=", ">
      {log.attachments.map((attachment, i) => (
        <InlineSearchParamLink
          key={i}
          onClick={() =>
            onTableSearchParamChange("attachmentMimeType", attachment.mimeType)
          }
        >
          {attachment.mimeType}
        </InlineSearchParamLink>
      ))}
    </Breadcrumbs>
  );
}

function NodePathField({
  log,
  onTableSearchParamChange,
}: {
  log: Log;
  onTableSearchParamChange: TableSearchParamChangeHandler;
}) {
  return log.nodePath
    .map<React.ReactNode>((node) => (
      <InlineSearchParamLink
        key={node.ref}
        onClick={() => onTableSearchParamChange("nodeRef", node.ref)}
      >
        {node.name}
      </InlineSearchParamLink>
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
  const { fields, loading: fieldsLoading } = useLogFields(repoId, "columns");
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

export function sortFields(a: string, b: string) {
  const order: { [key: string]: number } = {
    savedAt: 0,
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
    attachmentType: 18,
    attachmentMimeType: 19,
    node: 20,
    tag: 21,
    tagType: 22,
    tagName: 23,
    tagRef: 24,
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
  onTableSearchParamChange: TableSearchParamChangeHandler,
  logTranslator: (type: string, key: string) => string,
) {
  const { t } = i18n;

  if (field === "savedAt")
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
          onTableSearchParamChange={onTableSearchParamChange}
        />
      ),
    };
  }

  if (field === "actor")
    return {
      accessor: "actor",
      title: t("log.actor"),
      render: (log: Log) => (
        <ActorField
          log={log}
          onTableSearchParamChange={onTableSearchParamChange}
        />
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
          onTableSearchParamChange={onTableSearchParamChange}
        />
      ),
    };

  if (field === "actorName")
    return {
      accessor: "actorName",
      title: t("log.actorName"),
      render: (log: Log) => (
        <ActorNameField
          log={log}
          onTableSearchParamChange={onTableSearchParamChange}
        />
      ),
    };

  if (field === "actorRef")
    return {
      accessor: "actorRef",
      title: t("log.actorRef"),
      render: (log: Log) => (
        <ActorRefField
          log={log}
          onTableSearchParamChange={onTableSearchParamChange}
        />
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
          onTableSearchParamChange={onTableSearchParamChange}
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
          onTableSearchParamChange={onTableSearchParamChange}
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
          onTableSearchParamChange={onTableSearchParamChange}
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
          onTableSearchParamChange={onTableSearchParamChange}
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
          onTableSearchParamChange={onTableSearchParamChange}
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
          onTableSearchParamChange={onTableSearchParamChange}
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
          onTableSearchParamChange={onTableSearchParamChange}
        />
      ),
    };

  if (field === "resourceRef")
    return {
      accessor: "resourceRef",
      title: t("log.resourceRef"),
      render: (log: Log) => (
        <ResourceRefField
          log={log}
          onTableSearchParamChange={onTableSearchParamChange}
        />
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
          onTableSearchParamChange={onTableSearchParamChange}
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
          onTableSearchParamChange={onTableSearchParamChange}
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
          onTableSearchParamChange={onTableSearchParamChange}
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
          onTableSearchParamChange={onTableSearchParamChange}
        />
      ),
    };

  if (field === "tagName")
    return {
      accessor: "tagName",
      title: t("log.tagNames"),
      render: (log: Log) => (
        <TagNamesField
          log={log}
          onTableSearchParamChange={onTableSearchParamChange}
        />
      ),
    };

  if (field === "tagRef")
    return {
      accessor: "tagRef",
      title: t("log.tagRefs"),
      render: (log: Log) => (
        <TagRefsField
          log={log}
          onTableSearchParamChange={onTableSearchParamChange}
        />
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
          onTableSearchParamChange={onTableSearchParamChange}
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
          onTableSearchParamChange={onTableSearchParamChange}
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
          onTableSearchParamChange={onTableSearchParamChange}
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
          onTableSearchParamChange={onTableSearchParamChange}
        />
      ),
    };

  if (field === "node")
    return {
      accessor: "node",
      title: t("log.node"),
      render: (log: Log) => (
        <NodePathField
          log={log}
          onTableSearchParamChange={onTableSearchParamChange}
        />
      ),
    };

  console.error(`Unknown field: ${field}`);
}

function buildDataTableColumns({
  repoId,
  onTableSearchParamChange,
  selectedColumns,
  onSelectedColumnsChange,
  logTranslator,
}: {
  repoId: string;
  onTableSearchParamChange: TableSearchParamChangeHandler;
  selectedColumns: string[];
  // NB: null means default columns
  onSelectedColumnsChange: (selectedColumns: string[] | null) => void;
  logTranslator: (type: string, key: string) => string;
}) {
  return [
    ...selectedColumns
      .toSorted(sortFields)
      .map((column) =>
        fieldToColumn(column, repoId, onTableSearchParamChange, logTranslator),
      )
      .filter((data) => !!data),
    {
      accessor: "columns",
      title: (
        // Disable the inherited bold font style
        <span style={{ fontWeight: "normal" }}>
          <ColumnSelector
            repoId={repoId}
            selected={selectedColumns}
            onColumnAdded={(name: string) =>
              onSelectedColumnsChange([...selectedColumns, name])
            }
            onColumnRemoved={(name: string) =>
              onSelectedColumnsChange(selectedColumns.filter((n) => n !== name))
            }
            onColumnReset={() => onSelectedColumnsChange(null)}
          />
        </span>
      ),
    },
  ];
}

function useLogSearchQuery(searchParams: LogSearchParams) {
  return useInfiniteQuery({
    queryKey: ["logs", searchParams.serialize()],
    queryFn: async ({ pageParam }: { pageParam: string | null }) =>
      await getLogs(pageParam, searchParams),
    enabled: !!searchParams.repoId,
    initialPageParam: null,
    getNextPageParam: (lastPage) => lastPage.nextCursor,
    staleTime: 0,
  });
}

export function LogTable({
  searchParams,
  onTableSearchParamChange,
  selectedColumns,
  onSelectedColumnsChange,
}: {
  searchParams: LogSearchParams;
  onTableSearchParamChange: TableSearchParamChangeHandler;
  selectedColumns: string[];
  onSelectedColumnsChange: (selectedColumns: string[] | null) => void;
}) {
  const { t } = useTranslation();
  const logTranslator = useLogTranslator(searchParams.repoId);
  const query = useLogSearchQuery(searchParams);
  const { setDisplayedLogId } = useLogNavigationState();

  if (query.error) {
    return (
      <div>
        {t("common.unexpectedError")}: {query.error.message}
      </div>
    );
  }

  const logs = query.data?.pages.flatMap((page) => page.logs);

  return (
    <>
      <Stack>
        <DataTable
          columns={
            buildDataTableColumns({
              repoId: searchParams.repoId,
              onTableSearchParamChange,
              selectedColumns,
              onSelectedColumnsChange,
              logTranslator,
            }) as DataTableColumn<Log>[]
          }
          records={logs}
          onRowClick={({ record }) => setDisplayedLogId(record.id)}
          fetching={query.isFetching || query.isFetchingNextPage}
          minHeight={150}
          noRecordsText={t("log.list.noResults")}
        />
        {logs && logs.length > 0 && (
          <Center>
            <Button
              onClick={() => query.fetchNextPage()}
              disabled={!query.hasNextPage || query.isFetchingNextPage}
              loading={query.isFetchingNextPage}
            >
              {t("log.list.loadMore")}
            </Button>
          </Center>
        )}
      </Stack>
      <LogDetails repoId={searchParams.repoId} />
    </>
  );
}
