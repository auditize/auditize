import { useForm, isNotEmpty } from '@mantine/form';
import { TextInput, Code, Group, Button } from '@mantine/core';
import { createIntegration, updateIntegration, getIntegration, regenerateIntegrationToken } from '../api';
import { ResourceCreation, ResourceEdition } from '@/components/ResourceManagement';
import { useEffect, useState } from 'react';
import { CopyIcon } from '@/components/CopyIcon';
import { useMutation } from '@tanstack/react-query';
import { InlineErrorMessage } from '@/components/InlineErrorMessage';

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

function IntegrationForm({form}: {form: ReturnType<typeof useIntegrationForm>}) {
  return (
    <>
      <TextInput label="Name" placeholder="Name" data-autofocus {...form.getInputProps('name')}/>
    </>
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
    setToken(null);
  }, [opened]);

  return (
    <ResourceCreation
      title={"Create new integration"}
      form={form}
      opened={!!opened}
      onSave={() => createIntegration(form.values.name!)}
      onSaveSuccess={(data) => {
        const [_, token] = data as [string, string];
        setToken(token);
      }}
      isSaved={!!token}
      queryKeyForInvalidation={['integrations']}
    >
      <IntegrationForm form={form}/>
      {token && <Token value={token}/>}
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
      title={`Edit integration`}
      form={form}
      onSave={() => updateIntegration(integrationId!, form.values)}
      queryKeyForInvalidation={['integrations']}
    >
      <IntegrationForm form={form}/>
      <TokenRegeneration integrationId={integrationId!}/>
    </ResourceEdition>
  );
}
