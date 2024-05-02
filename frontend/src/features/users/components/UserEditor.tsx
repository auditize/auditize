import { useForm, isNotEmpty, isEmail, UseFormReturnType } from '@mantine/form';
import { TextInput } from '@mantine/core';
import { createUser, updateUser, getUser } from '../api';
import { ResourceCreation, ResourceEdition } from '@/components/ResourceManagement';
import { useAuthenticatedUser } from '@/features/auth';
import { WithPermissionManagement, emptyPermissions } from '@/features/permissions';
import { useEffect, useState } from 'react';

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

function UserEditor(
  {
    form,
    permissions,
    onChange,
    readOnly = false
  }:
  {
    form: UseFormReturnType<any>,
    permissions: Auditize.Permissions,
    onChange: (permissions: Auditize.Permissions) => void,
    readOnly?: boolean
  }
) {
  return (
    <WithPermissionManagement permissions={permissions} onChange={onChange} readOnly={readOnly}>
      <TextInput label="Firstname" placeholder="Firstname" data-autofocus {...form.getInputProps('firstName')} disabled={readOnly}/>
      <TextInput label="Lastname" placeholder="Lastname" data-autofocus {...form.getInputProps('lastName')} disabled={readOnly}/>
      <TextInput label="Email" placeholder="Email" data-autofocus {...form.getInputProps('email')} disabled={readOnly}/>
    </WithPermissionManagement>
  );
}

export function UserCreation({opened}: {opened?: boolean}) {
  const form = useUserForm({});
  const [permissions, setPermissions] = useState<Auditize.Permissions>(() => emptyPermissions());

  useEffect(() => {
    form.reset();
    setPermissions(emptyPermissions());
  }, [opened]);

  return (
    <ResourceCreation
      title={"Create new user"}
      opened={!!opened}
      onSubmit={form.onSubmit}
      onSave={() => createUser({...form.values, permissions})}
      queryKeyForInvalidation={['users']}
    >
      <UserEditor
        form={form}
        permissions={permissions}
        onChange={(perms) => setPermissions(perms)}
      />
    </ResourceCreation>
  );
}

export function UserEdition({userId}: {userId: string | null}) {
  const form = useUserForm({});
  const {currentUser} = useAuthenticatedUser();
  const [permissions, setPermissions] = useState<Auditize.Permissions>(() => emptyPermissions());
  const editSelf = userId === currentUser.id;

  return (
    <ResourceEdition
      resourceId={userId}
      queryKeyForLoad={['user', userId]}
      queryFnForLoad={() => getUser(userId!)}
      onDataLoaded={
        (data) => {
          form.setValues(data);
          setPermissions(data.permissions);
        }
      }
      title={`Edit user`}
      onSubmit={form.onSubmit}
      onSave={
        () => updateUser(userId!, {...form.values, permissions})
      }
      queryKeyForInvalidation={['users']}
      disabledSaving={editSelf}
    >
      <UserEditor
        form={form} 
        permissions={permissions}
        onChange={
          (perms) => {
            setPermissions(perms);
          }
        }
        readOnly={editSelf}
      />
    </ResourceEdition>
  );
}
