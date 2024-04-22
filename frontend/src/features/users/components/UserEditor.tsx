import { useForm, isNotEmpty, isEmail, UseFormReturnType } from '@mantine/form';
import { TextInput } from '@mantine/core';
import { createUser, updateUser, getUser } from '../api';
import { ResourceCreation, ResourceEdition } from '@/components/ResourceManagement';

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

function UserForm({form}: {form: UseFormReturnType<any>}) {
  return (
    <>
      <TextInput label="Firstname" placeholder="Firstname" data-autofocus {...form.getInputProps('firstName')}/>
      <TextInput label="Lastname" placeholder="Lastname" data-autofocus {...form.getInputProps('lastName')}/>
      <TextInput label="email" placeholder="email" data-autofocus {...form.getInputProps('email')}/>
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

  return (
    <ResourceEdition
      resourceId={userId}
      queryKeyForLoad={['user', userId]}
      queryFnForLoad={() => getUser(userId!)}
      title={`Edit user`}
      form={form}
      onSave={() => updateUser(userId!, form.values)}
      queryKeyForInvalidation={['users']}
    >
      <UserForm form={form}/>
    </ResourceEdition>
  );
}
