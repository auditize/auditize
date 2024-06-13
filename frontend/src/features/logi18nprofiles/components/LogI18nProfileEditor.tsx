import { FileInput, Stack, TextInput } from "@mantine/core";
import { isNotEmpty, useForm, UseFormReturnType } from "@mantine/form";
import { useEffect, useState } from "react";
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

function TranslationFile({
  lang,
  onChange,
}: {
  lang: string;
  onChange: (content: object | null) => void;
}) {
  const [file, setFile] = useState<File | null>(null);
  const fileReader = new FileReader();
  fileReader.onload = () => onChange(JSON.parse(fileReader.result as string));

  useEffect(() => {
    if (file) {
      fileReader.readAsText(file);
    } else {
      onChange(null);
    }
  }, [file]);

  return (
    <FileInput
      label="Translation file"
      placeholder="Select translation file"
      accept="application/json"
      value={file}
      onChange={setFile}
      clearable
    />
  );
}

function LogI18nProfileForm({
  form,
  onTranslationChange,
  readOnly = false,
}: {
  form: UseFormReturnType<any>;
  onTranslationChange: (lang: string, content: object | null) => void;
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
      <TranslationFile
        lang="fr"
        onChange={(content) => onTranslationChange("fr", content)}
      />
    </Stack>
  );
}

export function LogI18nProfileCreation({ opened }: { opened?: boolean }) {
  const { t } = useTranslation();
  const form = useLogI18nProfileForm({});
  const [translations, setTranslations] = useState<object>({});

  useEffect(() => {
    form.reset();
  }, [opened]);

  return (
    <ResourceCreation
      title={t("logi18nprofile.create.title")}
      opened={!!opened}
      onSubmit={form.onSubmit}
      onSave={() => createLogi18nProfile({ ...form.values, translations })}
      queryKeyForInvalidation={["logi18nprofiles"]}
    >
      <LogI18nProfileForm
        form={form}
        onTranslationChange={(lang, translation) => {
          setTranslations({
            ...translations,
            [lang]: translation ? translation : undefined,
          });
        }}
      />
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
  const [translations, setTranslations] = useState<object>({});

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
      onSave={() =>
        updateLogi18nProfile(profileId!, { ...form.values, translations })
      }
      queryKeyForInvalidation={["logi18nprofiles"]}
      disabledSaving={readOnly}
    >
      <LogI18nProfileForm
        form={form}
        readOnly={readOnly}
        onTranslationChange={(lang, translation) => {
          setTranslations({
            ...translations,
            [lang]: translation ? translation : undefined,
          });
        }}
      />
    </ResourceEdition>
  );
}
