import { useForm, isNotEmpty, isEmail, UseFormReturnType } from '@mantine/form';
import { TextInput } from '@mantine/core';
import { createUser, updateUser, getUser } from '../api';
import { ResourceCreation, ResourceEdition } from '@/components/ResourceManagement';
import { useAuthenticatedUser, useCurrentUser } from '@/features/auth';
import { WithPermissionManagement } from '@/features/permissions/components/WithPermissionManagement';
import { useEffect } from 'react';

function useUserForm(values: {name?: string}) {
  return useForm({
    initialValues: {
      firstName: '',
      lastName: '',
      email: '',
      ...values
    },
    validate: {
      firstName: isNotEmpty('Firstname is required'),
      lastName: isNotEmpty('Lastname is required'),
      email: isEmail('Email is required'),
    }
  });
}

function UserForm({form, readonly = false}: {form: UseFormReturnType<any>, readonly?: boolean}) {
  return (
    <WithPermissionManagement>
      <TextInput label="Firstname" placeholder="Firstname" data-autofocus {...form.getInputProps('firstName')} disabled={readonly}/>
      <TextInput label="Lastname" placeholder="Lastname" data-autofocus {...form.getInputProps('lastName')} disabled={readonly}/>
      <TextInput label="Email" placeholder="Email" data-autofocus {...form.getInputProps('email')} disabled={readonly}/>
    </WithPermissionManagement>
  );
}

export function UserCreation({opened}: {opened?: boolean}) {
  const form = useUserForm({});

  useEffect(() => {
    form.reset();
  }, [opened]);

  return (
    <ResourceCreation
      title={"Create new user"}
      opened={!!opened}
      onSubmit={form.onSubmit}
      onSave={() => createUser(form.values.firstName, form.values.lastName, form.values.email)}
      queryKeyForInvalidation={['users']}
    >
      <UserForm form={form}/>
    </ResourceCreation>
  );
}

export function UserEdition({userId}: {userId: string | null}) {
  const form = useUserForm({});
  const {currentUser} = useAuthenticatedUser();
  const editSelf = userId === currentUser.id;

  return (
    <ResourceEdition
      resourceId={userId}
      queryKeyForLoad={['user', userId]}
      queryFnForLoad={() => getUser(userId!)}
      onDataLoaded={(data) => form.setValues(data)}
      title={`Edit user`}
      onSubmit={form.onSubmit}
      onSave={() => updateUser(userId!, form.values)}
      queryKeyForInvalidation={['users']}
      disabledSaving={editSelf}
    >
      <UserForm form={form} readonly={editSelf}/>
    </ResourceEdition>
  );
}
