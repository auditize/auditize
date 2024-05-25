import {
  ActionIcon,
  Button,
  Flex,
  Group,
  Space,
  Stack,
  TextInput,
  useCombobox,
} from "@mantine/core";
import { useDisclosure, useLocalStorage } from "@mantine/hooks";
import { IconPlus } from "@tabler/icons-react";
import { useQuery } from "@tanstack/react-query";
import { useEffect, useReducer, useState } from "react";

import { CustomDateTimePicker, PaginatedSelector } from "@/components";
import { CustomMultiSelect } from "@/components/CustomMultiSelect";
import { RemovablePopover } from "@/components/RemovablePopover";
import { getAllMyRepos } from "@/features/repos";
import { Repo } from "@/features/repos";
import { labelize } from "@/utils/format";

import {
  buildLogSearchParams,
  getAllLogActionCategories,
  getAllLogActionTypes,
  getAllLogActorCustomFields,
  getAllLogActorTypes,
  getAllLogDetailFields,
  getAllLogResourceCustomFields,
  getAllLogResourceTypes,
  getAllLogSourceFields,
  getAllLogTagTypes,
  LogSearchParams,
} from "../api";
import { NodeSelector } from "./NodeSelector";

const FIXED_FILTER_NAMES = new Set([
  "date",
  "actionCategory",
  "actionType",
  "node",
]);

function RepoSelector({
  repoId,
  onChange,
}: {
  repoId?: string;
  onChange: (value: string) => void;
}) {
  const [defaultSelectedRepo, setDefaultSelectedRepo] = useLocalStorage({
    key: "default-selected-repo",
    getInitialValueInEffect: false,
  });

  // Update default-selected-repo local storage key on repoId change
  // so that the repo selector will be automatically set to the last selected repo
  // on page reload
  useEffect(() => {
    if (repoId) {
      setDefaultSelectedRepo(repoId);
    }
  }, [repoId]);

  return (
    <PaginatedSelector
      label="Repository"
      queryKey={["repos"]}
      queryFn={() => getAllMyRepos({ hasReadPermission: true })}
      selectedItem={repoId}
      clearable={false}
      onChange={onChange}
      onDataLoaded={(repos: Repo[]) => {
        // repo has not been auto-selected yet
        if (!repoId) {
          // if no default repo or default repo is not in the list, select the first one (if any)
          if (
            !defaultSelectedRepo ||
            !repos.find((repo) => repo.id === defaultSelectedRepo)
          ) {
            if (repos.length > 0) {
              onChange(repos[0].id);
            }
            // otherwise, select the default/previously selected repo (local storage)
          } else {
            onChange(defaultSelectedRepo);
          }
        }
      }}
      itemLabel={(repo) => repo.name}
      itemValue={(repo) => repo.id}
    />
  );
}

function useAvailableFilterFields(repoId: string) {
  const { data: actorCustomFields } = useQuery({
    queryKey: ["logActorCustomFields", repoId],
    queryFn: () => getAllLogActorCustomFields(repoId),
    enabled: !!repoId,
  });
  const { data: resourceCustomFields } = useQuery({
    queryKey: ["logResourceCustomFields", repoId],
    queryFn: () => getAllLogResourceCustomFields(repoId),
    enabled: !!repoId,
  });
  const { data: detailFields } = useQuery({
    queryKey: ["logDetailFields", repoId],
    queryFn: () => getAllLogDetailFields(repoId),
    enabled: !!repoId,
  });
  const { data: sourceFields } = useQuery({
    queryKey: ["logSourceFields", repoId],
    queryFn: () => getAllLogSourceFields(repoId),
    enabled: !!repoId,
  });

  const _ = ({ value, label }: { value: string; label: string }) => ({
    value,
    label,
    disabled: FIXED_FILTER_NAMES.has(value),
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
          _({ value: "actorType", label: "Actor type" }),
          _({ value: "actorName", label: "Actor name" }),
          _({ value: "actorRef", label: "Actor ref" }),
          ...(actorCustomFields ?? []).map((field) =>
            _({
              value: `actor.${field}`,
              label: `Actor ${field}`,
            }),
          ),
        ],
      },
      {
        group: "Source",
        items: (sourceFields ?? []).map((field) =>
          _({
            value: `source.${field}`,
            label: field,
          }),
        ),
      },
      {
        group: "Resource",
        items: [
          _({ value: "resourceType", label: "Resource type" }),
          _({ value: "resourceName", label: "Resource name" }),
          _({ value: "resourceRef", label: "Resource ref" }),
          ...(resourceCustomFields ?? []).map((field) =>
            _({
              value: `resource.${field}`,
              label: `Resource ${field}`,
            }),
          ),
        ],
      },
      {
        group: "Details",
        items: (detailFields ?? []).map((field) =>
          _({
            value: `details.${field}`,
            label: field,
          }),
        ),
      },
      {
        group: "Tag",
        items: [
          _({ value: "tagType", label: "Tag type" }),
          _({ value: "tagName", label: "Tag name" }),
          _({ value: "tagRef", label: "Tag ref" }),
        ],
      },
      {
        group: "Node",
        items: [_({ value: "node", label: "Node" })],
      },
    ],
  };
}

function FilterFieldSelect({
  label,
  searchParams,
  searchParamName,
  items,
  openedByDefault,
  onChange,
  onRemove,
}: {
  label: string;
  searchParams: LogSearchParams;
  searchParamName: string;
  items: (repoId: string) => Promise<string[]>;
  openedByDefault: boolean;
  onChange: (name: string, value: any) => void;
  onRemove: (name: string) => void;
}) {
  const [opened, { toggle }] = useDisclosure(openedByDefault);
  const value = searchParams[
    searchParamName as keyof LogSearchParams
  ] as string;
  return (
    <RemovablePopover
      title={label}
      opened={opened}
      isSet={!!value}
      onChange={toggle}
      removable={!FIXED_FILTER_NAMES.has(searchParamName)}
      onRemove={() => onRemove(searchParamName)}
    >
      <PaginatedSelector.WithoutDropdown
        label={label}
        queryKey={["logConsolidatedData", searchParamName, searchParams.repoId]}
        queryFn={() => items(searchParams.repoId!)}
        enabled={!!searchParams.repoId}
        selectedItem={value}
        onChange={(value) => onChange(searchParamName, value)}
        itemLabel={(item) => labelize(item)}
        itemValue={(item) => item}
      />
    </RemovablePopover>
  );
}

function BaseFilterFieldTextInput({
  label,
  name,
  value,
  openedByDefault,
  onChange,
  onRemove,
}: {
  label: string;
  name: string;
  value: string;
  openedByDefault: boolean;
  onChange: (value: any) => void;
  onRemove: (name: string) => void;
}) {
  const [opened, { toggle }] = useDisclosure(openedByDefault);
  return (
    <RemovablePopover
      title={label}
      opened={opened}
      isSet={!!value}
      onChange={toggle}
      removable={!FIXED_FILTER_NAMES.has(name)}
      onRemove={() => onRemove(name)}
    >
      <TextInput
        placeholder={label}
        value={value}
        onChange={(event) => onChange(event.currentTarget.value)}
      />
    </RemovablePopover>
  );
}

function FilterFieldTextInput({
  label,
  searchParams,
  searchParamName,
  openedByDefault,
  onChange,
  onRemove,
}: {
  label: string;
  searchParams: LogSearchParams;
  searchParamName: string;
  openedByDefault: boolean;
  onChange: (name: string, value: any) => void;
  onRemove: (name: string) => void;
}) {
  const value = searchParams[
    searchParamName as keyof LogSearchParams
  ] as string;
  return (
    <BaseFilterFieldTextInput
      label={label}
      name={searchParamName}
      value={value}
      openedByDefault={openedByDefault}
      onChange={(value) => onChange(searchParamName, value)}
      onRemove={onRemove}
    />
  );
}

function FilterField({
  name,
  searchParams,
  openedByDefault,
  onChange,
  onRemove,
}: {
  name: string;
  searchParams: LogSearchParams;
  openedByDefault: boolean;
  onChange: (name: string, value: any) => void;
  onRemove: (name: string) => void;
}) {
  if (name === "date") {
    const [opened, { toggle }] = useDisclosure(openedByDefault);
    return (
      <RemovablePopover
        title="Date"
        removable={!FIXED_FILTER_NAMES.has("date")}
        onRemove={() => onRemove("date")}
        isSet={!!(searchParams.since || searchParams.until)}
        opened={opened}
        onChange={toggle}
      >
        <Stack>
          <CustomDateTimePicker
            placeholder="From"
            value={searchParams.since}
            onChange={(value) => onChange("since", value)}
          />
          <CustomDateTimePicker
            placeholder="To"
            value={searchParams.until}
            onChange={(value) => onChange("until", value)}
            initToEndOfDay
          />
        </Stack>
      </RemovablePopover>
    );
  }

  if (name === "actionCategory") {
    return (
      <FilterFieldSelect
        label="Action category"
        searchParams={searchParams}
        searchParamName="actionCategory"
        items={getAllLogActionCategories}
        openedByDefault={openedByDefault}
        onChange={onChange}
        onRemove={onRemove}
      />
    );
  }

  if (name === "actionType") {
    return (
      <FilterFieldSelect
        label="Action type"
        searchParams={searchParams}
        searchParamName="actionType"
        items={(repoId) =>
          getAllLogActionTypes(repoId, searchParams.actionCategory!)
        }
        openedByDefault={openedByDefault}
        onChange={onChange}
        onRemove={onRemove}
      />
    );
  }

  if (name === "actorType") {
    return (
      <FilterFieldSelect
        label="Actor type"
        searchParams={searchParams}
        searchParamName="actorType"
        items={getAllLogActorTypes}
        openedByDefault={openedByDefault}
        onChange={onChange}
        onRemove={onRemove}
      />
    );
  }

  if (name === "actorName") {
    return (
      <FilterFieldTextInput
        label="Actor name"
        searchParams={searchParams}
        searchParamName="actorName"
        openedByDefault={openedByDefault}
        onChange={onChange}
        onRemove={onRemove}
      />
    );
  }

  if (name === "actorRef") {
    return (
      <FilterFieldTextInput
        label="Actor ref"
        searchParams={searchParams}
        searchParamName="actorRef"
        openedByDefault={openedByDefault}
        onChange={onChange}
        onRemove={onRemove}
      />
    );
  }

  if (name.startsWith("actor.")) {
    const fieldName = name.replace("actor.", "");
    return (
      <BaseFilterFieldTextInput
        label={`Actor ${labelize(fieldName)}`}
        name={name}
        value={searchParams.actorExtra!.get(fieldName) ?? ""}
        openedByDefault={openedByDefault}
        onChange={(value) =>
          onChange(
            "actorExtra",
            new Map([...searchParams.actorExtra!, [fieldName, value]]),
          )
        }
        onRemove={onRemove}
      />
    );
  }

  if (name.startsWith("source.")) {
    const fieldName = name.replace("source.", "");
    return (
      <BaseFilterFieldTextInput
        label={labelize(fieldName)}
        name={name}
        value={searchParams.source!.get(fieldName) ?? ""}
        openedByDefault={openedByDefault}
        onChange={(value) =>
          onChange(
            "source",
            new Map([...searchParams.source!, [fieldName, value]]),
          )
        }
        onRemove={onRemove}
      />
    );
  }

  if (name === "resourceType") {
    return (
      <FilterFieldSelect
        label="Resource type"
        searchParams={searchParams}
        searchParamName="resourceType"
        items={getAllLogResourceTypes}
        openedByDefault={openedByDefault}
        onChange={onChange}
        onRemove={onRemove}
      />
    );
  }

  if (name === "resourceName") {
    return (
      <FilterFieldTextInput
        label="Resource name"
        searchParams={searchParams}
        searchParamName="resourceName"
        openedByDefault={openedByDefault}
        onChange={onChange}
        onRemove={onRemove}
      />
    );
  }

  if (name === "resourceRef") {
    return (
      <FilterFieldTextInput
        label="Resource ref"
        searchParams={searchParams}
        searchParamName="resourceRef"
        openedByDefault={openedByDefault}
        onChange={onChange}
        onRemove={onRemove}
      />
    );
  }

  if (name.startsWith("resource.")) {
    const fieldName = name.replace("resource.", "");
    return (
      <BaseFilterFieldTextInput
        label={`Resource ${labelize(fieldName)}`}
        name={name}
        value={searchParams.resourceExtra!.get(fieldName) ?? ""}
        openedByDefault={openedByDefault}
        onChange={(value) =>
          onChange(
            "resourceExtra",
            new Map([...searchParams.resourceExtra!, [fieldName, value]]),
          )
        }
        onRemove={onRemove}
      />
    );
  }

  if (name.startsWith("details.")) {
    const fieldName = name.replace("details.", "");
    return (
      <BaseFilterFieldTextInput
        label={labelize(fieldName)}
        name={name}
        value={searchParams.details!.get(fieldName) ?? ""}
        openedByDefault={openedByDefault}
        onChange={(value) =>
          onChange(
            "details",
            new Map([...searchParams.details!, [fieldName, value]]),
          )
        }
        onRemove={onRemove}
      />
    );
  }

  if (name === "tagType") {
    return (
      <FilterFieldSelect
        label="Tag type"
        searchParams={searchParams}
        searchParamName="tagType"
        items={getAllLogTagTypes}
        openedByDefault={openedByDefault}
        onChange={onChange}
        onRemove={onRemove}
      />
    );
  }

  if (name === "tagName") {
    return (
      <FilterFieldTextInput
        label="Tag name"
        searchParams={searchParams}
        searchParamName="tagName"
        openedByDefault={openedByDefault}
        onChange={onChange}
        onRemove={onRemove}
      />
    );
  }

  if (name === "tagRef") {
    return (
      <FilterFieldTextInput
        label="Tag ref"
        searchParams={searchParams}
        searchParamName="tagRef"
        openedByDefault={openedByDefault}
        onChange={onChange}
        onRemove={onRemove}
      />
    );
  }

  if (name === "node") {
    const [opened, { toggle }] = useDisclosure(openedByDefault);
    return (
      <RemovablePopover
        title="Node"
        opened={opened}
        isSet={!!searchParams.nodeRef}
        onChange={toggle}
        removable={!FIXED_FILTER_NAMES.has("node")}
        onRemove={() => onRemove("node")}
      >
        <NodeSelector
          repoId={searchParams.repoId || null}
          nodeRef={searchParams.nodeRef || null}
          onChange={(value) => onChange("nodeRef", value)}
        />
      </RemovablePopover>
    );
  }

  return null;
}

function FilterFields({
  names,
  added,
  searchParams,
  onChange,
  onRemove,
}: {
  names: Set<string>;
  added: string | null;
  searchParams: LogSearchParams;
  onChange: (name: string, value: any) => void;
  onRemove: (name: string) => void;
}) {
  return (
    <>
      {Array.from(names).map((name) => (
        <FilterField
          key={name}
          name={name}
          searchParams={searchParams}
          openedByDefault={name === added}
          onChange={onChange}
          onRemove={onRemove}
        />
      ))}
    </>
  );
}

function FilterSelector({
  repoId,
  selected,
  onFilterAdded,
  onFilterRemoved,
}: {
  repoId: string;
  selected: Set<string>;
  onFilterAdded: (name: string) => void;
  onFilterRemoved: (name: string) => void;
}) {
  const { fields: availableFields } = useAvailableFilterFields(repoId);
  const comboboxStore = useCombobox();

  return (
    <CustomMultiSelect
      comboboxStore={comboboxStore}
      data={availableFields}
      value={Array.from(selected)}
      onOptionSubmit={onFilterAdded}
      onRemove={onFilterRemoved}
    >
      <Button onClick={() => comboboxStore.toggleDropdown()}>
        <IconPlus />
      </Button>
    </CustomMultiSelect>
  );
}

interface SetParamAction {
  type: "setParam";
  name: string;
  value: any;
}

interface ResetParamsAction {
  type: "resetParams";
  params?: LogSearchParams;
}

function filterParamsReducer(
  state: LogSearchParams,
  action: SetParamAction | ResetParamsAction,
): LogSearchParams {
  console.log("filterParamsReducer", action);
  switch (action.type) {
    case "setParam":
      const update = { [action.name]: action.value };
      if (action.name === "actionCategory") {
        update["actionType"] = "";
      }
      return { ...state, ...update };
    case "resetParams":
      const newParams = buildLogSearchParams();
      return action.params ? { ...newParams, ...action.params } : newParams;
  }
}

function searchParamsToFilterNames(searchParams: LogSearchParams): Set<string> {
  const filterNames = new Set<string>(FIXED_FILTER_NAMES);

  // Date
  if (searchParams.since || searchParams.until) {
    filterNames.add("date");
  }

  // Action
  if (searchParams.actionCategory) {
    filterNames.add("actionCategory");
  }
  if (searchParams.actionType) {
    filterNames.add("actionType");
  }

  // Actor
  if (searchParams.actorRef) {
    filterNames.add("actorRef");
  }
  if (searchParams.actorType) {
    filterNames.add("actorType");
  }
  if (searchParams.actorName) {
    filterNames.add("actorName");
  }
  searchParams.actorExtra!.forEach((_, name) => {
    filterNames.add("actor." + name);
  });

  // Source
  searchParams.source!.forEach((_, name) => {
    filterNames.add("source." + name);
  });

  // Resource
  if (searchParams.resourceRef) {
    filterNames.add("resourceRef");
  }
  if (searchParams.resourceType) {
    filterNames.add("resourceType");
  }
  if (searchParams.resourceName) {
    filterNames.add("resourceName");
  }
  searchParams.resourceExtra!.forEach((_, name) => {
    filterNames.add("resource." + name);
  });

  // Details
  searchParams.details!.forEach((_, name) => {
    filterNames.add("details." + name);
  });

  // Tag
  if (searchParams.tagRef) {
    filterNames.add("tagRef");
  }
  if (searchParams.tagType) {
    filterNames.add("tagType");
  }
  if (searchParams.tagName) {
    filterNames.add("tagName");
  }

  // Node
  if (searchParams.nodeRef) {
    filterNames.add("node");
  }

  return filterNames;
}

function removeSearchParam(
  filterName: string,
  searchParams: LogSearchParams,
  setSearchParam: (name: string, value: any) => void,
) {
  // Handle search params whose names are equivalent to filter names
  const equivalentSearchParams = [
    "actionCategory",
    "actionType",
    "actorRef",
    "actorType",
    "actorName",
    "resourceRef",
    "resourceType",
    "resourceName",
    "tagRef",
    "tagType",
    "tagName",
    "nodeRef",
  ];
  if (equivalentSearchParams.includes(filterName)) {
    setSearchParam(filterName, "");
    return;
  }

  // Handle date
  if (filterName === "date") {
    setSearchParam("since", null);
    setSearchParam("until", null);
    return;
  }

  // Handle source
  if (filterName.startsWith("source.")) {
    const fieldName = filterName.replace("source.", "");
    setSearchParam(
      "source",
      new Map([...searchParams.source!].filter(([name]) => name !== fieldName)),
    );
    return;
  }

  // Handle details
  if (filterName.startsWith("details.")) {
    const fieldName = filterName.replace("details.", "");
    setSearchParam(
      "details",
      new Map(
        [...searchParams.details!].filter(([name]) => name !== fieldName),
      ),
    );
    return;
  }

  // Handle actor custom fields
  if (filterName.startsWith("actor.")) {
    const fieldName = filterName.replace("actor.", "");
    setSearchParam(
      "actorExtra",
      new Map(
        [...searchParams.actorExtra!].filter(([name]) => name !== fieldName),
      ),
    );
    return;
  }

  // Handle resource custom fields
  if (filterName.startsWith("resource.")) {
    const fieldName = filterName.replace("resource.", "");
    setSearchParam(
      "resourceExtra",
      new Map(
        [...searchParams.resourceExtra!].filter(([name]) => name !== fieldName),
      ),
    );
    return;
  }

  // Handle node
  if (filterName === "node") {
    setSearchParam("nodeRef", "");
    return;
  }

  throw new Error(`Unknown filter name: ${filterName}`);
}

export function LogFilters({
  params,
  onChange,
}: {
  params: LogSearchParams;
  onChange: (filter: LogSearchParams) => void;
}) {
  const [editedParams, dispatch] = useReducer(filterParamsReducer, params);
  const [filterNames, setFilterNames] = useState<Set<string>>(
    searchParamsToFilterNames(params),
  );
  const [addedFilterName, setAddedFilterName] = useState<string | null>(null);

  // Typically, an inline filter has been applied from logs table
  useEffect(() => {
    dispatch({ type: "resetParams", params });
    setFilterNames(searchParamsToFilterNames(params));
  }, [params]);

  const removeFilter = (name: string) => {
    setFilterNames(new Set([...filterNames].filter((n) => n !== name)));
    removeSearchParam(name, editedParams, (name, value) =>
      dispatch({ type: "setParam", name, value }),
    );
  };

  return (
    <Flex justify="space-between" align="center">
      <Group gap="xs">
        {/* Repository selector */}
        <RepoSelector
          repoId={editedParams.repoId}
          onChange={(repoId) => {
            // Trigger a log search when the log repository is selected for the first time
            // so that the logs table can be populated when the page is loaded without any explicit filter
            if (!editedParams.repoId) {
              onChange({ ...editedParams, repoId });
            } else {
              dispatch({ type: "setParam", name: "repoId", value: repoId });
            }
          }}
        />

        {/* Filters */}
        <FilterFields
          names={filterNames}
          added={addedFilterName}
          searchParams={editedParams}
          onChange={(name, value) =>
            dispatch({ type: "setParam", name, value })
          }
          onRemove={removeFilter}
        />
        <FilterSelector
          repoId={editedParams.repoId!}
          selected={filterNames}
          onFilterAdded={(name) => {
            setFilterNames(new Set([...filterNames, name]));
            setAddedFilterName(name);
          }}
          onFilterRemoved={removeFilter}
        />
      </Group>

      {/* Apply & clear buttons */}
      <Space w="l" />
      <Group>
        <Button onClick={() => onChange(editedParams)}>Apply</Button>
        <Button
          onClick={() =>
            dispatch({
              type: "resetParams",
              params: { repoId: editedParams.repoId },
            })
          }
          variant="default"
        >
          Clear
        </Button>
      </Group>
    </Flex>
  );
}
