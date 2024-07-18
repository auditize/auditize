import { Stack, TextInput } from "@mantine/core";
import { isNotEmpty, useForm, UseFormReturnType } from "@mantine/form";
import { useQuery } from "@tanstack/react-query";
import { useEffect } from "react";
import { useTranslation } from "react-i18next";

import {
  ResourceCreation,
  ResourceEdition,
} from "@/components/ResourceManagement";

import { createLogFilter } from "../api";

function useLogFilterForm(values: { name?: string }) {
  const { t } = useTranslation();
  return useForm({
    initialValues: {
      name: "",
    },
    validate: {
      name: isNotEmpty(t("log.filter.form.name.required")),
    },
  });
}

function LogFilterForm({
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
        label={t("log.filter.form.name.label")}
        placeholder={t("log.filter.form.name.placeholder")}
        data-autofocus
        disabled={readOnly}
        {...form.getInputProps("name")}
      />
    </Stack>
  );
}

export function LogFilterCreation({
  repoId,
  searchParams,
  columns,
  opened,
  onClose,
}: {
  repoId: string;
  searchParams: Record<string, string>;
  columns: string[];
  opened?: boolean;
  onClose?: () => void;
}) {
  const { t } = useTranslation();
  const form = useLogFilterForm({});

  useEffect(() => {
    form.reset();
  }, [opened]);

  return (
    <ResourceCreation
      title={t("log.filter.create.title")}
      opened={!!opened}
      onClose={onClose}
      onSubmit={form.onSubmit}
      onSave={() =>
        createLogFilter({
          ...form.values,
          repoId,
          searchParams,
          columns,
        })
      }
      queryKeyForInvalidation={["repos"]}
    >
      <LogFilterForm form={form} />
    </ResourceCreation>
  );
}
