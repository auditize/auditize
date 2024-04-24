import { useForm, isNotEmpty } from '@mantine/form';
import { TextInput, Code, Group } from '@mantine/core';
import { createIntegration, updateIntegration, getIntegration } from '../api';
import { ResourceCreation, ResourceEdition } from '@/components/ResourceManagement';
import { useEffect, useState } from 'react';
import { CopyIcon } from '@/components/CopyIcon';

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
    </ResourceEdition>
  );
}
