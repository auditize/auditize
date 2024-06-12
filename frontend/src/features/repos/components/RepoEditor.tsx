import { Group, Radio, Stack, TextInput } from "@mantine/core";
import { isNotEmpty, useForm, UseFormReturnType } from "@mantine/form";
import { useEffect } from "react";
import { useTranslation } from "react-i18next";

import {
  ResourceCreation,
  ResourceEdition,
} from "@/components/ResourceManagement";

import { createRepo, getRepo, RepoStatus, updateRepo } from "../api";

function useRepoForm(values: { name?: string; status?: RepoStatus }) {
  const { t } = useTranslation();
  return useForm({
    initialValues: {
      name: "",
      status: "enabled" as RepoStatus,
      ...values,
    },
    validate: {
      name: isNotEmpty(t("repo.form.name.required")),
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
  const { t } = useTranslation();

  return (
    <Stack gap={"sm"}>
      <TextInput
        label={t("repo.form.name.label")}
        placeholder={t("repo.form.name.placeholder")}
        data-autofocus
        disabled={readOnly}
        {...form.getInputProps("name")}
      />
      <Radio.Group
        label={t("repo.form.status.label")}
        {...form.getInputProps("status")}
      >
        <Group mt="xs">
          <Radio
            value="enabled"
            label={t("repo.form.status.value.enabled")}
            disabled={readOnly}
          />
          <Radio
            value="readonly"
            label={t("repo.form.status.value.readonly")}
            disabled={readOnly}
          />
          <Radio
            value="disabled"
            label={t("repo.form.status.value.disabled")}
            disabled={readOnly}
          />
        </Group>
      </Radio.Group>
    </Stack>
  );
}

export function RepoCreation({ opened }: { opened?: boolean }) {
  const { t } = useTranslation();
  const form = useRepoForm({});

  useEffect(() => {
    form.reset();
  }, [opened]);

  return (
    <ResourceCreation
      title={t("repo.create.title")}
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
  const { t } = useTranslation();
  const form = useRepoForm({});

  return (
    <ResourceEdition
      resourceId={repoId}
      queryKeyForLoad={["repo", repoId]}
      queryFnForLoad={() => getRepo(repoId!)}
      onDataLoaded={(data) => {
        const { name, status } = data;
        form.setValues({ name, status });
      }}
      title={t("repo.edit.title")}
      onSubmit={form.onSubmit}
      onSave={() => updateRepo(repoId!, form.values)}
      queryKeyForInvalidation={["repos"]}
      disabledSaving={readOnly}
    >
      <RepoForm form={form} readOnly={readOnly} />
    </ResourceEdition>
  );
}
