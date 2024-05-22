import { Button, Code, Group, TextInput } from "@mantine/core";
import { isNotEmpty, useForm, UseFormReturnType } from "@mantine/form";
import { useMutation } from "@tanstack/react-query";
import { useEffect, useState } from "react";

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
      <BaseApikeyForm form={form} readOnly={readOnly} />
      {children}
    </WithPermissionManagement>
  );
}

function Key({ value }: { value: string }) {
  return (
    <Group>
      <span>Key: </span>
      <Code>{value}</Code>
      <CopyIcon value={value} />
    </Group>
  );
}

export function ApikeyCreation({ opened }: { opened?: boolean }) {
  const form = useApikeyForm();
  const [permissions, setPermissions] = useState<Permissions>(() =>
    emptyPermissions(),
  );
  const [key, setKey] = useState<string | null>(null);

  useEffect(() => {
    form.reset();
    setKey(null);
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
        setKey(key);
      }}
      queryKeyForInvalidation={["apikeys"]}
      disabledSaving={!!key}
    >
      <ApikeyEditor
        form={form}
        permissions={permissions}
        onChange={(perms) => setPermissions(perms)}
      >
        {key && <Key value={key} />}
      </ApikeyEditor>
    </ResourceCreation>
  );
}

export function KeyRegeneration({ apikeyId }: { apikeyId: string }) {
  const [newKey, setNewKey] = useState<string | null>(null);
  const [error, setError] = useState<string>("");
  const mutation = useMutation({
    mutationFn: () => regenerateApikey(apikeyId),
    onSuccess: (value) => setNewKey(value),
    onError: (error) => setError(error.message),
  });

  if (newKey) {
    return <Key value={newKey} />;
  } else {
    return (
      <>
        <Button onClick={() => mutation.mutate()}>Regenerate key</Button>
        <InlineErrorMessage>{error}</InlineErrorMessage>
      </>
    );
  }
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
        form.setValues(data);
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
        {!readOnly && <KeyRegeneration apikeyId={apikeyId!} />}
      </ApikeyEditor>
    </ResourceEdition>
  );
}
