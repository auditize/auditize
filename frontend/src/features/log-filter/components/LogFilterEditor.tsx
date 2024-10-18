import { Stack, Switch, TextInput } from "@mantine/core";
import { isNotEmpty, useForm, UseFormReturnType } from "@mantine/form";
import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import {
  ResourceCreation,
  ResourceEdition,
} from "@/components/ResourceManagement";

import { createLogFilter, getLogFilter, updateLogFilter } from "../api";

function useLogFilterForm(values: { name?: string }) {
  const { t } = useTranslation();
  return useForm({
    initialValues: {
      name: "",
      isFavorite: false,
    },
    validate: {
      name: isNotEmpty(t("log.filter.form.name.required")),
    },
  });
}

function LogFilterForm({ form }: { form: UseFormReturnType<any> }) {
  const { t } = useTranslation();

  return (
    <Stack gap={"sm"}>
      <TextInput
        label={t("log.filter.form.name.label")}
        placeholder={t("log.filter.form.name.placeholder")}
        data-autofocus
        {...form.getInputProps("name")}
      />
      <Switch.Group
        label={t("log.filter.form.isFavorite.label")}
        value={form.values.isFavorite ? ["isFavorite"] : []}
        onChange={(values) => {
          form.setFieldValue("isFavorite", values.includes("isFavorite"));
        }}
      >
        <Switch
          label={t("log.filter.form.isFavorite.placeholder")}
          value="isFavorite"
        />
      </Switch.Group>
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
  onClose: () => void;
}) {
  const { t } = useTranslation();
  const form = useLogFilterForm({});
  const navigate = useNavigate();

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
      onSaveSuccess={(filterId) => {
        onClose();
        navigate(`/logs?filterId=${filterId}`);
      }}
      queryKeyForInvalidation={["logFilters"]}
    >
      <LogFilterForm form={form} />
    </ResourceCreation>
  );
}

export function LogFilterEdition({
  filterId,
  onClose,
}: {
  filterId: string | null;
  onClose: () => void;
}) {
  const { t } = useTranslation();
  const form = useLogFilterForm({});

  return (
    <ResourceEdition
      resourceId={filterId}
      onClose={onClose}
      queryKeyForLoad={["logFilters", filterId]}
      queryFnForLoad={() => getLogFilter(filterId!)}
      onDataLoaded={(data) => {
        const { name, isFavorite } = data;
        form.setValues({ name, isFavorite });
      }}
      title={t("log.filter.edit.title")}
      onSubmit={form.onSubmit}
      onSave={() => updateLogFilter(filterId!, form.values)}
      queryKeyForInvalidation={["logFilters"]}
    >
      <LogFilterForm form={form} />
    </ResourceEdition>
  );
}
