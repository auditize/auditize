import {
  ActionIcon,
  Anchor,
  Button,
  Center,
  Group,
  Stack,
  Text,
  Tooltip,
  useCombobox,
} from "@mantine/core";
import {
  IconCalendarClock,
  IconColumns3,
  IconCornerDownRight,
  IconCylinder,
  IconHierarchy,
  IconTags,
  IconUser,
} from "@tabler/icons-react";
import { useInfiniteQuery } from "@tanstack/react-query";
import i18n from "i18next";
import { DataTable, DataTableColumn } from "mantine-datatable";
import React from "react";
import { useTranslation } from "react-i18next";

import { CustomMultiSelect } from "@/components/CustomMultiSelect";
import { getLogs, Log } from "@/features/log/api";
import { LogDetails } from "@/features/log/components/LogDetails";
import { useLogNavigationState } from "@/features/log/components/LogNavigation";
import { useLogTranslator } from "@/features/log/components/LogTranslation";
import { useColumnFields } from "@/features/log/components/useLogFields";
import { LogSearchParams } from "@/features/log/LogSearchParams";
import { iconSize } from "@/utils/ui";

import {
  ActionCategoryField,
  ActionField,
  ActionTypeField,
} from "./ActionFields";
import {
  ActorCustomField,
  ActorField,
  ActorNameField,
  ActorRefField,
  ActorTypeField,
} from "./ActorFields";
import {
  AttachmentMimeTypesField,
  AttachmentNamesField,
  AttachmentTypesField,
} from "./AttachmentFields";
import { DateField } from "./DateField";
import { DetailField } from "./DetailField";
import { EntityPathField } from "./EntityField";
import { TableSearchParamChangeHandler } from "./FieldUtils";
import {
  ResourceCustomField,
  ResourceField,
  ResourceNameField,
  ResourceRefField,
  ResourceTypeField,
} from "./ResourceFields";
import { SourceField } from "./SourceField";
import {
  TagNamesField,
  TagRefsField,
  TagsField,
  TagTypesField,
} from "./TagFields";

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
  const { fields, loading: fieldsLoading } = useColumnFields(repoId);
  const comboboxStore = useCombobox();
  const { logComponentRef } = useLogNavigationState();

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
      comboboxProps={{
        withinPortal: true,
        portalProps: { target: logComponentRef.current! },
        position: "bottom-end",
      }}
    >
      <Tooltip
        label={t("log.list.columnSelector.tooltip")}
        disabled={comboboxStore.dropdownOpened}
        position="bottom-end"
        withArrow
        withinPortal={false}
      >
        <ActionIcon
          onClick={() => comboboxStore.toggleDropdown()}
          loading={fieldsLoading}
          loaderProps={{ type: "dots" }}
          variant="transparent"
        >
          <IconColumns3 />
        </ActionIcon>
      </Tooltip>
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
    attachmentName: 17,
    attachmentType: 18,
    attachmentMimeType: 19,
    entity: 20,
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
  columnSelector: React.ReactNode | undefined,
) {
  const { t } = i18n;
  const columnTitle = (name: string, icon?: any, iconStyle?: any) => (
    <Group justify="space-between" wrap="nowrap">
      <span>
        {icon &&
          React.createElement(icon, {
            style: {
              ...iconSize(16),
              position: "relative",
              top: "2px",
              marginRight: "0.25rem",
              ...(iconStyle || {}),
            },
          })}
        {name}
      </span>
      {columnSelector}
    </Group>
  );
  const column = (props: DataTableColumn<Log>) => ({
    ...props,
    titleStyle: {
      background: "var(--auditize-header-color)",
    },
  });

  if (field === "savedAt")
    return column({
      accessor: "savedAt",
      title: columnTitle(t("log.date"), IconCalendarClock),
      render: (log: Log) => <DateField log={log} />,
    });

  if (field.startsWith("source.")) {
    const fieldName = field.split(".")[1];
    return column({
      accessor: `source.${fieldName}`,
      title: columnTitle(
        t("log.source") + ": " + logTranslator("source_field", fieldName),
      ),
      render: (log: Log) => (
        <SourceField
          log={log}
          fieldName={fieldName}
          repoId={repoId}
          onTableSearchParamChange={onTableSearchParamChange}
        />
      ),
    });
  }

  if (field === "actor")
    return column({
      accessor: "actor",
      title: columnTitle(t("log.actor"), IconUser),
      render: (log: Log) => (
        <ActorField
          log={log}
          onTableSearchParamChange={onTableSearchParamChange}
        />
      ),
    });

  if (field === "actorType")
    return column({
      accessor: "actorType",
      title: columnTitle(t("log.actorType")),
      render: (log: Log) => (
        <ActorTypeField
          log={log}
          repoId={repoId}
          onTableSearchParamChange={onTableSearchParamChange}
        />
      ),
    });

  if (field === "actorName")
    return column({
      accessor: "actorName",
      title: columnTitle(t("log.actorName")),
      render: (log: Log) => (
        <ActorNameField
          log={log}
          onTableSearchParamChange={onTableSearchParamChange}
        />
      ),
    });

  if (field === "actorRef")
    return column({
      accessor: "actorRef",
      title: columnTitle(t("log.actorRef")),
      render: (log: Log) => (
        <ActorRefField
          log={log}
          onTableSearchParamChange={onTableSearchParamChange}
        />
      ),
    });

  if (field.startsWith("actor.")) {
    const fieldName = field.split(".")[1];
    return column({
      accessor: `actor.${fieldName}`,
      title: columnTitle(
        t("log.actor") + ": " + logTranslator("actor_custom_field", fieldName),
      ),
      render: (log: Log) => (
        <ActorCustomField
          log={log}
          repoId={repoId}
          fieldName={fieldName}
          onTableSearchParamChange={onTableSearchParamChange}
        />
      ),
    });
  }

  if (field === "action")
    return column({
      accessor: "action",
      title: columnTitle(t("log.action"), IconCornerDownRight),
      render: (log: Log) => (
        <ActionField
          log={log}
          repoId={repoId}
          onTableSearchParamChange={onTableSearchParamChange}
        />
      ),
    });

  if (field === "actionType")
    return column({
      accessor: "actionType",
      title: columnTitle(t("log.actionType")),
      render: (log: Log) => (
        <ActionTypeField
          log={log}
          repoId={repoId}
          onTableSearchParamChange={onTableSearchParamChange}
        />
      ),
    });

  if (field === "actionCategory")
    return column({
      accessor: "actionCategory",
      title: columnTitle(t("log.actionCategory")),
      render: (log: Log) => (
        <ActionCategoryField
          log={log}
          repoId={repoId}
          onTableSearchParamChange={onTableSearchParamChange}
        />
      ),
    });

  if (field === "resource")
    return column({
      accessor: "resource",
      title: columnTitle(t("log.resource"), IconCylinder),
      render: (log: Log) => (
        <ResourceField
          log={log}
          repoId={repoId}
          onTableSearchParamChange={onTableSearchParamChange}
        />
      ),
    });

  if (field === "resourceType")
    return column({
      accessor: "resourceType",
      title: columnTitle(t("log.resourceType")),
      render: (log: Log) => (
        <ResourceTypeField
          log={log}
          repoId={repoId}
          onTableSearchParamChange={onTableSearchParamChange}
        />
      ),
    });

  if (field === "resourceName")
    return column({
      accessor: "resourceName",
      title: columnTitle(t("log.resourceName")),
      render: (log: Log) => (
        <ResourceNameField
          log={log}
          onTableSearchParamChange={onTableSearchParamChange}
        />
      ),
    });

  if (field === "resourceRef")
    return column({
      accessor: "resourceRef",
      title: columnTitle(t("log.resourceRef")),
      render: (log: Log) => (
        <ResourceRefField
          log={log}
          onTableSearchParamChange={onTableSearchParamChange}
        />
      ),
    });

  if (field.startsWith("resource.")) {
    const fieldName = field.split(".")[1];
    return column({
      accessor: `resource.${fieldName}`,
      title: columnTitle(
        t("log.resource") +
          ": " +
          logTranslator("resource_custom_field", fieldName),
      ),
      render: (log: Log) => (
        <ResourceCustomField
          log={log}
          repoId={repoId}
          fieldName={fieldName}
          onTableSearchParamChange={onTableSearchParamChange}
        />
      ),
    });
  }

  if (field.startsWith("details.")) {
    const fieldName = field.split(".")[1];
    return column({
      accessor: `details.${fieldName}`,
      title: columnTitle(logTranslator("detail_field", fieldName)),
      render: (log: Log) => (
        <DetailField
          log={log}
          repoId={repoId}
          fieldName={fieldName}
          onTableSearchParamChange={onTableSearchParamChange}
        />
      ),
    });
  }

  if (field === "tag")
    return column({
      accessor: "tags",
      title: columnTitle(t("log.tags"), IconTags, { top: "3px" }),
      render: (log: Log) => (
        <TagsField
          log={log}
          repoId={repoId}
          onTableSearchParamChange={onTableSearchParamChange}
        />
      ),
    });

  if (field === "tagType")
    return column({
      accessor: "tagType",
      title: columnTitle(t("log.tagTypes")),
      render: (log: Log) => (
        <TagTypesField
          log={log}
          repoId={repoId}
          onTableSearchParamChange={onTableSearchParamChange}
        />
      ),
    });

  if (field === "tagName")
    return column({
      accessor: "tagName",
      title: columnTitle(t("log.tagNames")),
      render: (log: Log) => (
        <TagNamesField
          log={log}
          onTableSearchParamChange={onTableSearchParamChange}
        />
      ),
    });

  if (field === "tagRef")
    return column({
      accessor: "tagRef",
      title: columnTitle(t("log.tagRefs")),
      render: (log: Log) => (
        <TagRefsField
          log={log}
          onTableSearchParamChange={onTableSearchParamChange}
        />
      ),
    });

  if (field === "attachment")
    return column({
      accessor: "attachment",
      title: columnTitle(t("log.attachments")),
      // NB: display attachments like attachment types for now
      render: (log: Log) => (
        <AttachmentTypesField
          log={log}
          repoId={repoId}
          onTableSearchParamChange={onTableSearchParamChange}
        />
      ),
    });

  if (field === "attachmentName")
    return column({
      accessor: "attachmentName",
      title: columnTitle(t("log.attachmentNames")),
      render: (log: Log) => (
        <AttachmentNamesField
          log={log}
          onTableSearchParamChange={onTableSearchParamChange}
        />
      ),
    });

  if (field === "attachmentType")
    return column({
      accessor: "attachmentType",
      title: columnTitle(t("log.attachmentTypes")),
      render: (log: Log) => (
        <AttachmentTypesField
          log={log}
          repoId={repoId}
          onTableSearchParamChange={onTableSearchParamChange}
        />
      ),
    });

  if (field === "attachmentMimeType")
    return column({
      accessor: "attachmentMimeType",
      title: columnTitle(t("log.attachmentMimeTypes")),
      render: (log: Log) => (
        <AttachmentMimeTypesField
          log={log}
          onTableSearchParamChange={onTableSearchParamChange}
        />
      ),
    });

  if (field === "entity")
    return column({
      accessor: "entity",
      title: columnTitle(t("log.entity"), IconHierarchy),
      render: (log: Log) => (
        <EntityPathField
          log={log}
          onTableSearchParamChange={onTableSearchParamChange}
        />
      ),
    });

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
  const columnSelector = (
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
  );

  return selectedColumns
    .toSorted(sortFields)
    .map((column, i) =>
      fieldToColumn(
        column,
        repoId,
        onTableSearchParamChange,
        logTranslator,
        i + 1 == selectedColumns.length ? columnSelector : undefined,
      ),
    )
    .filter((data) => !!data);
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
    gcTime: 0,
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
          highlightOnHover
          withTableBorder
          verticalAlign="top"
          verticalSpacing="md"
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
