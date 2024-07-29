import { ActionIcon, Stack, TextInput } from "@mantine/core";
import { isNotEmpty, useForm, UseFormReturnType } from "@mantine/form";
import { IconRefresh } from "@tabler/icons-react";
import { useMutation } from "@tanstack/react-query";
import { t } from "i18next";
import { ReactElement, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { CopyIcon } from "@/components/CopyIcon";
import { InlineErrorMessage } from "@/components/InlineErrorMessage";
import {
  ResourceCreation,
  ResourceEdition,
} from "@/components/ResourceManagement";
import {
  emptyPermissions,
  WithPermissionManagement,
} from "@/features/permissions";
import { Permissions } from "@/features/permissions/types";

import {
  createApikey,
  getApikey,
  regenerateApikey,
  updateApikey,
} from "../api";

function useApikeyForm() {
  const { t } = useTranslation();
  return useForm({
    initialValues: {
      name: "",
    },
    validate: {
      name: isNotEmpty(t("apikey.form.name.required")),
    },
  });
}

function useApiKeyEditorState(opened: boolean) {
  const form = useApikeyForm();
  const [permissions, setPermissions] = useState<Permissions>(() =>
    emptyPermissions(),
  );

  useEffect(() => {
    if (!opened) {
      form.reset();
      setPermissions(emptyPermissions());
    }
  }, [opened]);

  return { form, permissions, setPermissions };
}

function BaseApikeyForm({
  form,
  readOnly,
}: {
  form: ReturnType<typeof useApikeyForm>;
  readOnly: boolean;
}) {
  const { t } = useTranslation();
  return (
    <>
      <TextInput
        label={t("apikey.form.name.label")}
        placeholder={t("apikey.form.name.placeholder")}
        data-autofocus
        disabled={readOnly}
        {...form.getInputProps("name")}
      />
    </>
  );
}

function ApikeyEditor({
  form,
  permissions,
  onChange,
  children,
  readOnly = false,
}: {
  form: UseFormReturnType<any>;
  permissions: Permissions;
  onChange: (permissions: Permissions) => void;
  children: React.ReactNode;
  readOnly?: boolean;
}) {
  return (
    <WithPermissionManagement
      permissions={permissions}
      onChange={onChange}
      readOnly={readOnly}
    >
      <Stack gap={"sm"}>
        <BaseApikeyForm form={form} readOnly={readOnly} />
        {children}
      </Stack>
    </WithPermissionManagement>
  );
}

function Secret({ value, button }: { value: string; button?: ReactElement }) {
  const { t } = useTranslation();
  return (
    <TextInput
      label={t("apikey.form.key.label")}
      disabled
      value={value}
      rightSection={button}
    />
  );
}

function SecretCreation({ value }: { value: string | null }) {
  const { t } = useTranslation();
  return (
    <Secret
      value={value || t("apikey.form.key.placeholder.create")}
      button={value ? <CopyIcon value={value} /> : undefined}
    />
  );
}

function SecretUpdate({ apikeyId }: { apikeyId: string }) {
  const { t } = useTranslation();
  const [secret, setSecret] = useState<string | null>(null);
  const [error, setError] = useState<string>("");
  const mutation = useMutation({
    mutationFn: () => regenerateApikey(apikeyId),
    onSuccess: (value) => setSecret(value),
    onError: (error) => setError(error.message),
  });

  if (secret) {
    return <Secret value={secret} button={<CopyIcon value={secret} />} />;
  } else {
    return (
      <>
        <Secret
          value={t("apikey.form.key.placeholder.update")}
          button={
            <ActionIcon
              onClick={() => mutation.mutate()}
              variant="subtle"
              size="sm"
            >
              <IconRefresh />
            </ActionIcon>
          }
        />
        <InlineErrorMessage>{error}</InlineErrorMessage>
      </>
    );
  }
}

export function ApikeyCreation({
  opened,
  onClose,
}: {
  opened?: boolean;
  onClose: () => void;
}) {
  const { t } = useTranslation();
  const { form, permissions, setPermissions } = useApiKeyEditorState(!!opened);
  const [secret, setSecret] = useState<string | null>(null);

  useEffect(() => {
    if (!opened) {
      setSecret(null);
    }
  }, [opened]);

  return (
    <ResourceCreation
      title={t("apikey.create.title")}
      opened={!!opened}
      onClose={onClose}
      onSubmit={form.onSubmit}
      onSave={() => createApikey({ ...form.values, permissions })}
      onSaveSuccess={(data) => {
        const [_, key] = data as [string, string];
        setSecret(key);
      }}
      queryKeyForInvalidation={["apikeys"]}
      disabledSaving={!!secret}
    >
      <ApikeyEditor
        form={form}
        permissions={permissions}
        onChange={(perms) => setPermissions(perms)}
        readOnly={!!secret}
      >
        <SecretCreation value={secret} />
      </ApikeyEditor>
    </ResourceCreation>
  );
}

export function ApikeyEdition({
  apikeyId,
  onClose,
  readOnly,
}: {
  apikeyId: string | null;
  onClose: () => void;
  readOnly: boolean;
}) {
  const { form, permissions, setPermissions } =
    useApiKeyEditorState(!!apikeyId);

  return (
    <ResourceEdition
      resourceId={apikeyId}
      onClose={onClose}
      queryKeyForLoad={["apikey", apikeyId]}
      queryFnForLoad={() => getApikey(apikeyId!)}
      onDataLoaded={(data) => {
        const { name } = data;
        form.setValues({ name });
        setPermissions(data.permissions);
      }}
      title={t("apikey.edit.title")}
      onSubmit={form.onSubmit}
      onSave={() => updateApikey(apikeyId!, { ...form.values, permissions })}
      queryKeyForInvalidation={["apikeys"]}
      disabledSaving={readOnly}
    >
      <ApikeyEditor
        form={form}
        permissions={permissions}
        onChange={(perms) => {
          setPermissions(perms);
        }}
        readOnly={readOnly}
      >
        {!readOnly && <SecretUpdate apikeyId={apikeyId!} />}
      </ApikeyEditor>
    </ResourceEdition>
  );
}
