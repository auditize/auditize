import { ActionIcon, Stack, TextInput } from "@mantine/core";
import { isNotEmpty, useForm, UseFormReturnType } from "@mantine/form";
import { IconRefresh } from "@tabler/icons-react";
import { useMutation } from "@tanstack/react-query";
import { ReactElement, useEffect, useState } from "react";

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
  return useForm({
    initialValues: {
      name: "",
    },
    validate: {
      name: isNotEmpty("Name is required"),
    },
  });
}

function BaseApikeyForm({
  form,
  readOnly,
}: {
  form: ReturnType<typeof useApikeyForm>;
  readOnly: boolean;
}) {
  return (
    <>
      <TextInput
        label="Name"
        placeholder="Enter name"
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
  return (
    <TextInput
      label="Key (secret)"
      disabled
      value={value}
      rightSection={button}
    />
  );
}

function SecretCreation({ value }: { value: string | null }) {
  return (
    <Secret
      value={
        value || "The secret key will appear once the API key has been saved"
      }
      button={value ? <CopyIcon value={value} /> : undefined}
    />
  );
}

function SecretUpdate({ apikeyId }: { apikeyId: string }) {
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
          value={"You can generate a new key by clicking the refresh button"}
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

export function ApikeyCreation({ opened }: { opened?: boolean }) {
  const form = useApikeyForm();
  const [permissions, setPermissions] = useState<Permissions>(() =>
    emptyPermissions(),
  );
  const [secret, setSecret] = useState<string | null>(null);

  useEffect(() => {
    form.reset();
    setSecret(null);
    setPermissions(emptyPermissions());
  }, [opened]);

  return (
    <ResourceCreation
      title={"Create new API key"}
      opened={!!opened}
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
  readOnly,
}: {
  apikeyId: string | null;
  readOnly: boolean;
}) {
  const form = useApikeyForm();
  const [permissions, setPermissions] = useState<Permissions>(() =>
    emptyPermissions(),
  );

  return (
    <ResourceEdition
      resourceId={apikeyId}
      queryKeyForLoad={["apikey", apikeyId]}
      queryFnForLoad={() => getApikey(apikeyId!)}
      onDataLoaded={(data) => {
        const { name } = data;
        form.setValues({ name });
        setPermissions(data.permissions);
      }}
      title={`Edit API key`}
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
