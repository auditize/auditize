import { useForm, isNotEmpty, UseFormReturnType } from '@mantine/form';
import { TextInput } from '@mantine/core';
import { createRepo, updateRepo, getRepo } from '../api';
import { ResourceCreation, ResourceEdition } from '@/components/ResourceManagement';
import { useEffect } from 'react';

function useRepoForm(values: {name?: string}) {
  return useForm({
    initialValues: {
      name: '',
      ...values
    },
    validate: {
      name: isNotEmpty('Name is required')
    }
  });
}

function RepoForm({form}: {form: UseFormReturnType<any>}) {
  return (
    <>
      <TextInput label="Name" placeholder="Name" data-autofocus {...form.getInputProps('name')}/>
    </>
  );
}

export function RepoCreation({opened}: {opened?: boolean}) {
  const form = useRepoForm({});

  useEffect(() => {
    form.reset();
  }, [opened]);

  return (
    <ResourceCreation
      title={"Create new log repository"}
      opened={!!opened}
      onSubmit={form.onSubmit}
      onSave={() => createRepo(form.values)}
      queryKeyForInvalidation={['repos']}
    >
      <RepoForm form={form}/>
    </ResourceCreation>
  );
}

export function RepoEdition({repoId}: {repoId: string | null}) {
  const form = useRepoForm({});

  return (
    <ResourceEdition
      resourceId={repoId}
      queryKeyForLoad={['repo', repoId]}
      queryFnForLoad={() => getRepo(repoId!)}
      onDataLoaded={(data) => form.setValues(data)}
      title={`Edit log repository`}
      onSubmit={form.onSubmit}
      onSave={() => updateRepo(repoId!, {name: form.values.name})}
      queryKeyForInvalidation={['repos']}
    >
      <RepoForm form={form}/>
    </ResourceEdition>
  );
}
