import { useForm, isNotEmpty, UseFormReturnType } from '@mantine/form';
import { TextInput, Code, Group, Button } from '@mantine/core';
import { createIntegration, updateIntegration, getIntegration, regenerateIntegrationToken } from '../api';
import { ResourceCreation, ResourceEdition } from '@/components/ResourceManagement';
import { useEffect, useState } from 'react';
import { CopyIcon } from '@/components/CopyIcon';
import { useMutation } from '@tanstack/react-query';
import { InlineErrorMessage } from '@/components/InlineErrorMessage';
import { WithPermissionManagement, emptyPermissions } from '@/features/permissions';

function useIntegrationForm() {
  return useForm({
    initialValues: {
      name: '',
    },
    validate: {
      name: isNotEmpty('Name is required'),
    }
  });
}

function BaseIntegrationForm({form}: {form: ReturnType<typeof useIntegrationForm>}) {
  return (
    <>
      <TextInput label="Name" placeholder="Name" data-autofocus {...form.getInputProps('name')}/>
    </>
  );
}

function IntegrationEditor(
  {
    form,
    permissions,
    onChange,
    children,
  }:
  {
    form: UseFormReturnType<any>,
    permissions: Auditize.Permissions,
    onChange: (permissions: Auditize.Permissions) => void,
    children: React.ReactNode,
  }
) {
  return (
    <WithPermissionManagement permissions={permissions} onChange={onChange}>
      <BaseIntegrationForm form={form}/>
      {children}
    </WithPermissionManagement>
  );
}

function Token({value}: {value: string}) {
  return (
    <Group>
      <span>Token: </span>
      <Code>{value}</Code>
      <CopyIcon value={value}/>
    </Group>
  );
}

export function IntegrationCreation({opened}: {opened?: boolean}) {
  const form = useIntegrationForm();
  const [permissions, setPermissions] = useState<Auditize.Permissions>(() => emptyPermissions());
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    form.reset();
    setToken(null);
  }, [opened]);

  return (
    <ResourceCreation
      title={"Create new integration"}
      opened={!!opened}
      onSubmit={form.onSubmit}
      onSave={() => createIntegration({...form.values, permissions})}
      onSaveSuccess={(data) => {
        const [_, token] = data as [string, string];
        setToken(token);
      }}
      queryKeyForInvalidation={['integrations']}
      disabledSaving={!!token}
    >
      <IntegrationEditor
        form={form}
        permissions={permissions}
        onChange={(perms) => setPermissions(perms)}
      >
        {token && <Token value={token}/>}
      </IntegrationEditor>
    </ResourceCreation>
  );
}

export function TokenRegeneration({integrationId}: {integrationId: string}) {
  const [newToken, setNewToken] = useState<string | null>(null);
  const [error, setError] = useState<string>("");
  const mutation = useMutation({
    mutationFn: () => regenerateIntegrationToken(integrationId),
    onSuccess: (value) => setNewToken(value),
    onError: (error) => setError(error.message)
  });

  if (newToken) {
    return <Token value={newToken}/>;
  } else {
    return (
      <>
        <Button onClick={() => mutation.mutate()}>Regenerate token</Button>
        <InlineErrorMessage>{error}</InlineErrorMessage>
      </>
    );
  }
}

export function IntegrationEdition({integrationId}: {integrationId: string | null}) {
  const form = useIntegrationForm();
  const [permissions, setPermissions] = useState<Auditize.Permissions>(() => emptyPermissions());

  return (
    <ResourceEdition
      resourceId={integrationId}
      queryKeyForLoad={['integration', integrationId]}
      queryFnForLoad={() => getIntegration(integrationId!)}
      onDataLoaded={
        (data) => {
          form.setValues(data);
          setPermissions(data.permissions);
        }
      }
      title={`Edit integration`}
      onSubmit={form.onSubmit}
      onSave={
        () => updateIntegration(integrationId!, {...form.values, permissions})
      }
      queryKeyForInvalidation={['integrations']}
    >
      <IntegrationEditor
        form={form}
        permissions={permissions}
        onChange={
          (perms) => {
            setPermissions(perms);
          }
        }
      >
        <TokenRegeneration integrationId={integrationId!}/>
      </IntegrationEditor>
    </ResourceEdition>
  );
}
