import { Stack, TextInput } from "@mantine/core";
import { isNotEmpty, useForm, UseFormReturnType } from "@mantine/form";
import { useEffect } from "react";
import { useTranslation } from "react-i18next";

import {
  ResourceCreation,
  ResourceEdition,
} from "@/components/ResourceManagement";

import {
  createLogi18nProfile,
  getLogI18nProfile,
  updateLogi18nProfile,
} from "../api";

function useLogI18nProfileForm(values: { name?: string }) {
  const { t } = useTranslation();
  return useForm({
    initialValues: {
      name: "",
      ...values,
    },
    validate: {
      name: isNotEmpty(t("logi18nprofile.form.name.required")),
    },
  });
}

function LogI18nProfileForm({
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
        label={t("logi18nprofile.form.name.label")}
        placeholder={t("logi18nprofile.form.name.placeholder")}
        data-autofocus
        disabled={readOnly}
        {...form.getInputProps("name")}
      />
    </Stack>
  );
}

export function LogI18nProfileCreation({ opened }: { opened?: boolean }) {
  const { t } = useTranslation();
  const form = useLogI18nProfileForm({});

  useEffect(() => {
    form.reset();
  }, [opened]);

  return (
    <ResourceCreation
      title={t("logi18nprofile.create.title")}
      opened={!!opened}
      onSubmit={form.onSubmit}
      onSave={() => createLogi18nProfile(form.values)}
      queryKeyForInvalidation={["logi18nprofiles"]}
    >
      <LogI18nProfileForm form={form} />
    </ResourceCreation>
  );
}

export function LogI18nProfileEdition({
  profileId,
  readOnly,
}: {
  profileId: string | null;
  readOnly: boolean;
}) {
  const { t } = useTranslation();
  const form = useLogI18nProfileForm({});

  return (
    <ResourceEdition
      resourceId={profileId}
      queryKeyForLoad={["logi18nprofile", profileId]}
      queryFnForLoad={() => getLogI18nProfile(profileId!)}
      onDataLoaded={(data) => {
        const { name } = data;
        form.setValues({ name });
      }}
      title={t("logi18nprofile.edit.title")}
      onSubmit={form.onSubmit}
      onSave={() => updateLogi18nProfile(profileId!, form.values)}
      queryKeyForInvalidation={["logi18nprofiles"]}
      disabledSaving={readOnly}
    >
      <LogI18nProfileForm form={form} readOnly={readOnly} />
    </ResourceEdition>
  );
}
