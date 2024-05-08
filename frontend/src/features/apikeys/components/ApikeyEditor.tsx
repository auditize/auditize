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

import {
  createApikey,
  getApikey,
  regenerateApikeyToken,
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
        placeholder="Name"
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
  permissions: Auditize.Permissions;
  onChange: (permissions: Auditize.Permissions) => void;
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

function Token({ value }: { value: string }) {
  return (
    <Group>
      <span>Token: </span>
      <Code>{value}</Code>
      <CopyIcon value={value} />
    </Group>
  );
}

export function ApikeyCreation({ opened }: { opened?: boolean }) {
  const form = useApikeyForm();
  const [permissions, setPermissions] = useState<Auditize.Permissions>(() =>
    emptyPermissions(),
  );
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    form.reset();
    setToken(null);
  }, [opened]);

  return (
    <ResourceCreation
      title={"Create new apikey"}
      opened={!!opened}
      onSubmit={form.onSubmit}
      onSave={() => createApikey({ ...form.values, permissions })}
      onSaveSuccess={(data) => {
        const [_, token] = data as [string, string];
        setToken(token);
      }}
      queryKeyForInvalidation={["apikeys"]}
      disabledSaving={!!token}
    >
      <ApikeyEditor
        form={form}
        permissions={permissions}
        onChange={(perms) => setPermissions(perms)}
      >
        {token && <Token value={token} />}
      </ApikeyEditor>
    </ResourceCreation>
  );
}

export function TokenRegeneration({ apikeyId }: { apikeyId: string }) {
  const [newToken, setNewToken] = useState<string | null>(null);
  const [error, setError] = useState<string>("");
  const mutation = useMutation({
    mutationFn: () => regenerateApikeyToken(apikeyId),
    onSuccess: (value) => setNewToken(value),
    onError: (error) => setError(error.message),
  });

  if (newToken) {
    return <Token value={newToken} />;
  } else {
    return (
      <>
        <Button onClick={() => mutation.mutate()}>Regenerate token</Button>
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
  const [permissions, setPermissions] = useState<Auditize.Permissions>(() =>
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
      title={`Edit apikey`}
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
        {!readOnly && <TokenRegeneration apikeyId={apikeyId!} />}
      </ApikeyEditor>
    </ResourceEdition>
  );
}
