import { Button, FileInput, Input, Stack, TextInput } from "@mantine/core";
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

function EditableTranslationFile({
  lang,
  content,
  onChange,
}: {
  lang: string;
  content: object | null;
  onChange: (content: object | null) => void;
}) {
  return content ? (
    <Input.Wrapper label="Translation file">
      <br />
      <Button onClick={() => onChange(null)}>Remove</Button>
    </Input.Wrapper>
  ) : (
    <TranslationFile lang={lang} onChange={onChange} />
  );
}

function LogI18nProfileForm({
  form,
  readOnly = false,
  children,
}: {
  form: UseFormReturnType<any>;
  readOnly?: boolean;
  children: React.ReactNode;
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
      {children}
    </Stack>
  );
}

export function LogI18nProfileCreation({ opened }: { opened?: boolean }) {
  const { t } = useTranslation();
  const form = useLogI18nProfileForm({});
  const [translations, setTranslations] = useState<Record<string, object>>({});

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
      <LogI18nProfileForm form={form}>
        <TranslationFile
          lang="fr"
          onChange={(translation) => {
            setTranslations(
              translation
                ? { ...translations, fr: translation }
                : Object.fromEntries(
                    Object.entries(translations).filter(
                      ([key]) => key !== "fr",
                    ),
                  ),
            );
          }}
        />
      </LogI18nProfileForm>
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
  const [translations, setTranslations] = useState<
    Record<string, object | null>
  >({});

  return (
    <ResourceEdition
      resourceId={profileId}
      queryKeyForLoad={["logi18nprofile", profileId]}
      queryFnForLoad={() => getLogI18nProfile(profileId!)}
      onDataLoaded={(data) => {
        const { name, translations } = data;
        form.setValues({ name });
        setTranslations(translations);
      }}
      title={t("logi18nprofile.edit.title")}
      onSubmit={form.onSubmit}
      onSave={() =>
        updateLogi18nProfile(profileId!, { ...form.values, translations })
      }
      queryKeyForInvalidation={["logi18nprofiles"]}
      disabledSaving={readOnly}
    >
      <LogI18nProfileForm form={form} readOnly={readOnly}>
        <EditableTranslationFile
          lang="fr"
          content={translations.fr}
          onChange={(translation) => {
            setTranslations({
              ...translations,
              fr: translation ? translation : null,
            });
          }}
        />
      </LogI18nProfileForm>
    </ResourceEdition>
  );
}
