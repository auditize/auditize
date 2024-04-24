import { useForm, isNotEmpty, isEmail, UseFormReturnType } from '@mantine/form';
import { TextInput } from '@mantine/core';
import { createIntegration, updateIntegration, getIntegration } from '../api';
import { ResourceCreation, ResourceEdition } from '@/components/ResourceManagement';

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

export function IntegrationCreation({opened}: {opened?: boolean}) {
  const form = useIntegrationForm();

  return (
    <ResourceCreation
      title={"Create new integration"}
      form={form}
      opened={!!opened}
      onSave={() => createIntegration(form.values.name!)}
      queryKeyForInvalidation={['integrations']}
    >
      <IntegrationForm form={form}/>
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
