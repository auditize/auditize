import { Group, Radio, Stack, TextInput } from "@mantine/core";
import { isNotEmpty, useForm, UseFormReturnType } from "@mantine/form";
import { useEffect } from "react";

import {
  ResourceCreation,
  ResourceEdition,
} from "@/components/ResourceManagement";

import { createRepo, getRepo, RepoStatus, updateRepo } from "../api";

function useRepoForm(values: { name?: string; status?: RepoStatus }) {
  return useForm({
    initialValues: {
      name: "",
      status: "enabled" as RepoStatus,
      ...values,
    },
    validate: {
      name: isNotEmpty("Name is required"),
    },
  });
}

function RepoForm({
  form,
  readOnly = false,
}: {
  form: UseFormReturnType<any>;
  readOnly?: boolean;
}) {
  return (
    <Stack gap={"sm"}>
      <TextInput
        label="Name"
        placeholder="Enter name"
        data-autofocus
        disabled={readOnly}
        {...form.getInputProps("name")}
      />
      <Radio.Group label="Status" {...form.getInputProps("status")}>
        <Group mt="xs">
          <Radio value="enabled" label="Enabled" disabled={readOnly} />
          <Radio value="readonly" label="Read-only" disabled={readOnly} />
          <Radio value="disabled" label="Disabled" disabled={readOnly} />
        </Group>
      </Radio.Group>
    </Stack>
  );
}

export function RepoCreation({ opened }: { opened?: boolean }) {
  const form = useRepoForm({});

  useEffect(() => {
    form.reset();
  }, [opened]);

  return (
    <ResourceCreation
      title={"Create new log repository"}
      opened={!!opened}
      onSubmit={form.onSubmit}
      onSave={() => createRepo(form.values)}
      queryKeyForInvalidation={["repos"]}
    >
      <RepoForm form={form} />
    </ResourceCreation>
  );
}

export function RepoEdition({
  repoId,
  readOnly,
}: {
  repoId: string | null;
  readOnly: boolean;
}) {
  const form = useRepoForm({});

  return (
    <ResourceEdition
      resourceId={repoId}
      queryKeyForLoad={["repo", repoId]}
      queryFnForLoad={() => getRepo(repoId!)}
      onDataLoaded={(data) => form.setValues(data)}
      title={`Edit log repository`}
      onSubmit={form.onSubmit}
      onSave={() => updateRepo(repoId!, form.values)}
      queryKeyForInvalidation={["repos"]}
      disabledSaving={readOnly}
    >
      <RepoForm form={form} readOnly={readOnly} />
    </ResourceEdition>
  );
}
