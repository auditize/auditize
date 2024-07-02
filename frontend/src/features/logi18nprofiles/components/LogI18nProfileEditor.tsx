import {
  ActionIcon,
  CloseButton,
  FileInput,
  Group,
  Input,
  Stack,
  TextInput,
} from "@mantine/core";
import { isNotEmpty, useForm, UseFormReturnType } from "@mantine/form";
import { IconDownload } from "@tabler/icons-react";
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

function TranslationFileInput({
  profileId,
  lang,
  isSet,
  onChange,
  readonly = false,
}: {
  profileId?: string;
  lang: string;
  isSet?: boolean;
  onChange: (content: object | null) => void;
  readonly?: boolean;
}) {
  const { t } = useTranslation();
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
    <Input.Wrapper
      label={t("logi18nprofile.form.file.label", {
        lang: t("language." + lang),
      })}
    >
      <Group justify="space-between">
        <FileInput
          placeholder={
            isSet
              ? t("logi18nprofile.form.file.configured")
              : t("logi18nprofile.form.file.choose")
          }
          accept="application/json"
          value={file}
          onChange={setFile}
          disabled={readonly}
          flex={1}
        />
        {profileId && (
          <ActionIcon
            component="a"
            href={`http://localhost:8000/log-i18n-profiles/${profileId}/translations/${lang}`}
            download={`auditize-log-translation-${profileId}-${lang}.json`}
            target="_blank"
            variant="transparent"
            flex={0}
          >
            <IconDownload />
          </ActionIcon>
        )}
        <CloseButton
          onClick={() => {
            if (file) {
              setFile(null);
            } else {
              onChange(null);
            }
          }}
          disabled={readonly || (!isSet && !file)}
          flex={0}
        />
      </Group>
    </Input.Wrapper>
  );
}

function TranslationFileCreationInput({
  lang,
  translations,
  setTranslations,
}: {
  lang: string;
  translations: Record<string, object>;
  setTranslations: (translations: Record<string, object>) => void;
}) {
  return (
    <TranslationFileInput
      lang={lang}
      onChange={(translation) => {
        setTranslations(
          translation
            ? { ...translations, [lang]: translation }
            : Object.fromEntries(
                Object.entries(translations).filter(([key]) => key !== lang),
              ),
        );
      }}
    />
  );
}

function TranslationFileUpdateInput({
  profileId,
  lang,
  translations,
  setTranslations,
  readOnly,
}: {
  profileId: string;
  lang: string;
  translations: Record<string, object | null>;
  setTranslations: (translations: Record<string, object | null>) => void;
  readOnly: boolean;
}) {
  return (
    <TranslationFileInput
      profileId={profileId}
      lang={lang}
      isSet={!!translations[lang]}
      onChange={(translation) => {
        setTranslations({
          ...translations,
          // NB: in order to remove an existing translation, it must be explicitly set to null
          [lang]: translation ? translation : null,
        });
      }}
      readonly={readOnly}
    />
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
        <TranslationFileCreationInput
          lang="en"
          translations={translations}
          setTranslations={setTranslations}
        />
        <TranslationFileCreationInput
          lang="fr"
          translations={translations}
          setTranslations={setTranslations}
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
        <TranslationFileUpdateInput
          profileId={profileId!}
          lang="en"
          translations={translations}
          setTranslations={setTranslations}
          readOnly={readOnly}
        />
        <TranslationFileUpdateInput
          profileId={profileId!}
          lang="fr"
          translations={translations}
          setTranslations={setTranslations}
          readOnly={readOnly}
        />
      </LogI18nProfileForm>
    </ResourceEdition>
  );
}
