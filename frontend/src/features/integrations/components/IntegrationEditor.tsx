import { useForm, isNotEmpty } from '@mantine/form';
import { TextInput, Code, Group, Button } from '@mantine/core';
import { createIntegration, updateIntegration, getIntegration, regenerateIntegrationToken } from '../api';
import { ResourceCreation, ResourceEdition } from '@/components/ResourceManagement';
import { useEffect, useState } from 'react';
import { CopyIcon } from '@/components/CopyIcon';
import { useMutation } from '@tanstack/react-query';
import { InlineErrorMessage } from '@/components/InlineErrorMessage';
import { WithPermissionManagement } from '@/features/permissions/components/WithPermissionManagement';

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

function IntegrationForm({form, children}: {form: ReturnType<typeof useIntegrationForm>, children: React.ReactNode}) {
  return (
    <WithPermissionManagement>
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
      onSave={() => createIntegration(form.values.name!)}
      onSaveSuccess={(data) => {
        const [_, token] = data as [string, string];
        setToken(token);
      }}
      queryKeyForInvalidation={['integrations']}
      disabledSaving={!!token}
    >
      <IntegrationForm form={form}>
        {token && <Token value={token}/>}
      </IntegrationForm>
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

  return (
    <ResourceEdition
      resourceId={integrationId}
      queryKeyForLoad={['integration', integrationId]}
      queryFnForLoad={() => getIntegration(integrationId!)}
      onDataLoaded={(data) => form.setValues(data)}
      title={`Edit integration`}
      onSubmit={form.onSubmit}
      onSave={() => updateIntegration(integrationId!, form.values)}
      queryKeyForInvalidation={['integrations']}
    >
      <IntegrationForm form={form}>
        <TokenRegeneration integrationId={integrationId!}/>
      </IntegrationForm>
    </ResourceEdition>
  );
}
