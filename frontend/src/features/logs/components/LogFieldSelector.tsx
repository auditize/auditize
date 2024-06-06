import { Button, useCombobox } from "@mantine/core";
import { useQuery } from "@tanstack/react-query";

import { CustomMultiSelect } from "@/components/CustomMultiSelect";
import { labelize, titlize } from "@/utils/format";

import {
  getAllLogActorCustomFields,
  getAllLogDetailFields,
  getAllLogResourceCustomFields,
  getAllLogSourceFields,
} from "../api";

function useLogFields(
  repoId: string,
  fixedFields: Set<string> | undefined,
  enableCompositeFields: boolean,
) {
  const { data: actorCustomFields, isPending: actorCustomFieldsPending } =
    useQuery({
      queryKey: ["logActorCustomFields", repoId],
      queryFn: () => getAllLogActorCustomFields(repoId),
      enabled: !!repoId,
    });
  const { data: resourceCustomFields, isPending: resourceCustomFieldsPending } =
    useQuery({
      queryKey: ["logResourceCustomFields", repoId],
      queryFn: () => getAllLogResourceCustomFields(repoId),
      enabled: !!repoId,
    });
  const { data: detailFields, isPending: detailFieldsPending } = useQuery({
    queryKey: ["logDetailFields", repoId],
    queryFn: () => getAllLogDetailFields(repoId),
    enabled: !!repoId,
  });
  const { data: sourceFields, isPending: sourceFieldsPending } = useQuery({
    queryKey: ["logSourceFields", repoId],
    queryFn: () => getAllLogSourceFields(repoId),
    enabled: !!repoId,
  });

  const _ = ({ value, label }: { value: string; label: string }) => ({
    value,
    label,
    disabled: fixedFields && fixedFields.has(value),
  });

  return {
    fields: [
      { group: "Date", items: [_({ value: "date", label: "Date" })] },
      {
        group: "Action",
        items: [
          _({ value: "actionCategory", label: "Action category" }),
          _({ value: "actionType", label: "Action type" }),
        ],
      },
      {
        group: "Actor",
        items: [
          ...(enableCompositeFields
            ? [_({ value: "actor", label: "Actor *" })]
            : []),
          _({ value: "actorType", label: "Actor type" }),
          _({ value: "actorName", label: "Actor name" }),
          _({ value: "actorRef", label: "Actor ref" }),
          ...(actorCustomFields ?? []).map((field) =>
            _({
              value: `actor.${field}`,
              label: `Actor ${labelize(field)}`,
            }),
          ),
        ],
      },
      {
        group: "Source",
        items: (sourceFields ?? []).map((field) =>
          _({
            value: `source.${field}`,
            label: titlize(field),
          }),
        ),
      },
      {
        group: "Resource",
        items: [
          ...(enableCompositeFields
            ? [_({ value: "resource", label: "Resource *" })]
            : []),
          _({ value: "resourceType", label: "Resource type" }),
          _({ value: "resourceName", label: "Resource name" }),
          _({ value: "resourceRef", label: "Resource ref" }),
          ...(resourceCustomFields ?? []).map((field) =>
            _({
              value: `resource.${field}`,
              label: `Resource ${labelize(field)}`,
            }),
          ),
        ],
      },
      {
        group: "Details",
        items: (detailFields ?? []).map((field) =>
          _({
            value: `details.${field}`,
            label: titlize(field),
          }),
        ),
      },
      {
        group: "Tag",
        items: [
          ...(enableCompositeFields
            ? [_({ value: "tag", label: "Tag *" })]
            : []),
          _({ value: "tagType", label: "Tag type" }),
          _({ value: "tagName", label: "Tag name" }),
          _({ value: "tagRef", label: "Tag ref" }),
        ],
      },
      {
        group: "Attachment",
        items: [
          _({ value: "attachmentName", label: "Attachment name" }),
          _({
            value: "attachmentDescription",
            label: "Attachment description",
          }),
          _({ value: "attachmentType", label: "Attachment type" }),
          _({ value: "attachmentMimeType", label: "Attachment MIME type" }),
        ],
      },
      {
        group: "Node",
        items: [_({ value: "node", label: "Node" })],
      },
    ],
    loading:
      actorCustomFieldsPending ||
      resourceCustomFieldsPending ||
      detailFieldsPending ||
      sourceFieldsPending,
  };
}

export function LogFieldSelector({
  repoId,
  selected,
  onSelected,
  onUnselected,
  fixed,
  enableCompositeFields = false,
  loading = false,
  children,
}: {
  repoId: string;
  selected: Set<string>;
  onSelected: (name: string) => void;
  onUnselected: (name: string) => void;
  fixed?: Set<string>;
  enableCompositeFields?: boolean;
  loading?: boolean;
  children: React.ReactNode;
}) {
  const { fields, loading: fieldsLoading } = useLogFields(
    repoId,
    fixed,
    enableCompositeFields,
  );
  const comboboxStore = useCombobox();

  return (
    <CustomMultiSelect
      comboboxStore={comboboxStore}
      data={fields}
      value={Array.from(selected)}
      onOptionSubmit={onSelected}
      onRemove={onUnselected}
    >
      <Button
        onClick={() => comboboxStore.toggleDropdown()}
        loading={fieldsLoading || loading}
        loaderProps={{ type: "dots" }}
      >
        {children}
      </Button>
    </CustomMultiSelect>
  );
}
