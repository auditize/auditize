import {
  ActionIcon,
  Group,
  NumberInput,
  Radio,
  rem,
  Select,
  SelectProps,
  Stack,
  TextInput,
  Tooltip,
} from "@mantine/core";
import type { ActionIconProps } from "@mantine/core";
import { isNotEmpty, useForm, UseFormReturnType } from "@mantine/form";
import { IconDownload } from "@tabler/icons-react";
import { useQuery } from "@tanstack/react-query";
import { useEffect } from "react";
import { useTranslation } from "react-i18next";

import {
  ResourceCreation,
  ResourceEdition,
} from "@/components/ResourceManagement";
import { getAllLogI18nProfiles } from "@/features/log-i18n-profile";

import { createRepo, getRepo, RepoStatus, updateRepo } from "../api";

function useRepoForm() {
  const { t } = useTranslation();
  return useForm({
    initialValues: {
      name: "",
      status: "enabled" as RepoStatus,
      logI18nProfileId: null as string | null,
      retentionPeriod: null as number | null,
    },
    validate: {
      name: isNotEmpty(t("repo.form.name.required")),
    },
    transformValues: (values) => ({
      ...values,
      retentionPeriod:
        (values.retentionPeriod as any) === "" ? null : values.retentionPeriod,
    }),
  });
}

function useRepoEditorState(opened: boolean) {
  const form = useRepoForm();

  useEffect(() => {
    if (!opened) {
      form.reset();
    }
  }, [opened]);

  return { form };
}

function LogI18nProfileSelector({
  form,
  readOnly,
  selectProps,
}: {
  form: UseFormReturnType<any>;
  readOnly: boolean;
  selectProps?: SelectProps;
}) {
  const { t } = useTranslation();
  const query = useQuery({
    queryKey: ["logi18nprofiles"],
    queryFn: getAllLogI18nProfiles,
  });

  return (
    <Select
      label={t("repo.form.logI18nProfile.label")}
      placeholder={
        query.isLoading
          ? t("common.loading")
          : query.error
            ? t("common.notCurrentlyAvailable")
            : t("repo.form.logI18nProfile.placeholder")
      }
      data={query.data?.map((profile) => ({
        label: profile.name,
        value: profile.id,
      }))}
      clearable
      disabled={readOnly}
      comboboxProps={{ shadow: "md" }}
      {...form.getInputProps("logI18nProfileId")}
      {...selectProps}
    />
  );
}

function LogTranslationTemplateDownload({
  repoId,
  iconProps,
}: {
  repoId?: string;
  iconProps?: ActionIconProps;
}) {
  const { t } = useTranslation();

  return (
    <Tooltip
      label={t("repo.form.downloadTranslationTemplate")}
      withArrow
      position="bottom"
    >
      <ActionIcon
        component="a"
        href={`/api/repos/${repoId}/translations/template`}
        download={`auditize-log-translation-template-${repoId}.json`}
        target="_blank"
        variant="transparent"
        {...iconProps}
      >
        <IconDownload />
      </ActionIcon>
    </Tooltip>
  );
}

function RepoForm({
  form,
  repoId,
  readOnly = false,
}: {
  form: UseFormReturnType<any>;
  repoId?: string;
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
        <Group>
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
      <NumberInput
        label={t("repo.form.retentionPeriod.label")}
        placeholder={t("repo.form.retentionPeriod.placeholder")}
        min={1}
        stepHoldDelay={500}
        stepHoldInterval={50}
        disabled={readOnly}
        {...form.getInputProps("retentionPeriod")}
      />
      <Group justify="space-between" align="flex-end">
        <LogI18nProfileSelector
          form={form}
          readOnly={readOnly}
          selectProps={{ flex: 1 }}
        />
        {repoId && (
          <LogTranslationTemplateDownload
            repoId={repoId}
            iconProps={{ flex: 0, style: { marginBottom: rem(4) } }}
          />
        )}
      </Group>
    </Stack>
  );
}

export function RepoCreation({
  opened,
  onClose,
}: {
  opened?: boolean;
  onClose: () => void;
}) {
  const { t } = useTranslation();
  const { form } = useRepoEditorState(!!opened);

  return (
    <ResourceCreation
      title={t("repo.create.title")}
      opened={!!opened}
      onClose={onClose}
      onSubmit={form.onSubmit}
      onSave={() => createRepo(form.getTransformedValues())}
      queryKeyForInvalidation={["repos"]}
    >
      <RepoForm form={form} />
    </ResourceCreation>
  );
}

export function RepoEdition({
  repoId,
  onClose,
  readOnly,
}: {
  repoId: string | null;
  onClose: () => void;
  readOnly: boolean;
}) {
  const { t } = useTranslation();
  const { form } = useRepoEditorState(!!repoId);

  return (
    <ResourceEdition
      resourceId={repoId}
      onClose={onClose}
      queryKeyForLoad={["repo", repoId]}
      queryFnForLoad={() => getRepo(repoId!)}
      onDataLoaded={(data) => {
        const { name, status, retentionPeriod, logI18nProfileId } = data;
        form.setValues({
          name,
          status,
          retentionPeriod: retentionPeriod ?? "",
          logI18nProfileId,
        });
      }}
      title={t("repo.edit.title")}
      onSubmit={form.onSubmit}
      onSave={() => updateRepo(repoId!, form.getTransformedValues())}
      queryKeyForInvalidation={["repos"]}
      disabledSaving={readOnly}
    >
      <RepoForm form={form} repoId={repoId ?? undefined} readOnly={readOnly} />
    </ResourceEdition>
  );
}
