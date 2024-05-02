import { useForm, isNotEmpty, isEmail, UseFormReturnType } from '@mantine/form';
import { TextInput } from '@mantine/core';
import { createUser, updateUser, getUser } from '../api';
import { ResourceCreation, ResourceEdition } from '@/components/ResourceManagement';
import { useAuthenticatedUser, useCurrentUser } from '@/features/auth';

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
    <>
      <TextInput label="Firstname" placeholder="Firstname" data-autofocus {...form.getInputProps('firstName')} disabled={readonly}/>
      <TextInput label="Lastname" placeholder="Lastname" data-autofocus {...form.getInputProps('lastName')} disabled={readonly}/>
      <TextInput label="Email" placeholder="Email" data-autofocus {...form.getInputProps('email')} disabled={readonly}/>
    </>
  );
}

export function UserCreation({opened}: {opened?: boolean}) {
  const form = useUserForm({});

  return (
    <ResourceCreation
      title={"Create new user"}
      form={form}
      opened={!!opened}
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
      title={`Edit user`}
      form={form}
      onSave={() => updateUser(userId!, form.values)}
      queryKeyForInvalidation={['users']}
      disabledSaving={editSelf}
    >
      <UserForm form={form} readonly={editSelf}/>
    </ResourceEdition>
  );
}
