import { Stack, TextInput } from "@mantine/core";
import { isEmail, isNotEmpty, useForm, UseFormReturnType } from "@mantine/form";
import { useEffect, useState } from "react";

import {
  ResourceCreation,
  ResourceEdition,
} from "@/components/ResourceManagement";
import {
  emptyPermissions,
  Permissions,
  WithPermissionManagement,
} from "@/features/permissions";

import { createUser, getUser, updateUser } from "../api";

function useUserForm(values: { name?: string }) {
  return useForm({
    initialValues: {
      firstName: "",
      lastName: "",
      email: "",
      ...values,
    },
    validate: {
      firstName: isNotEmpty("Firstname is required"),
      lastName: isNotEmpty("Lastname is required"),
      email: isEmail("Email is required"),
    },
  });
}

function UserEditor({
  form,
  permissions,
  onChange,
  readOnly = false,
}: {
  form: UseFormReturnType<any>;
  permissions: Permissions;
  onChange: (permissions: Permissions) => void;
  readOnly?: boolean;
}) {
  return (
    <WithPermissionManagement
      permissions={permissions}
      onChange={onChange}
      readOnly={readOnly}
    >
      <Stack gap={"sm"}>
        <TextInput
          label="Firstname"
          placeholder="Enter firstname"
          data-autofocus
          {...form.getInputProps("firstName")}
          disabled={readOnly}
        />
        <TextInput
          label="Lastname"
          placeholder="Enter lastname"
          data-autofocus
          {...form.getInputProps("lastName")}
          disabled={readOnly}
        />
        <TextInput
          label="Email"
          placeholder="Enter email"
          data-autofocus
          {...form.getInputProps("email")}
          disabled={readOnly}
        />
      </Stack>
    </WithPermissionManagement>
  );
}

export function UserCreation({ opened }: { opened?: boolean }) {
  const form = useUserForm({});
  const [permissions, setPermissions] = useState<Permissions>(() =>
    emptyPermissions(),
  );

  useEffect(() => {
    form.reset();
    setPermissions(emptyPermissions());
  }, [opened]);

  return (
    <ResourceCreation
      title={"Create new user"}
      opened={!!opened}
      onSubmit={form.onSubmit}
      onSave={() => createUser({ ...form.values, permissions })}
      queryKeyForInvalidation={["users"]}
    >
      <UserEditor
        form={form}
        permissions={permissions}
        onChange={(perms) => setPermissions(perms)}
      />
    </ResourceCreation>
  );
}

export function UserEdition({
  userId,
  readOnly,
}: {
  userId: string | null;
  readOnly: boolean;
}) {
  const form = useUserForm({});
  const [permissions, setPermissions] = useState<Permissions>(() =>
    emptyPermissions(),
  );

  return (
    <ResourceEdition
      resourceId={userId}
      queryKeyForLoad={["user", userId]}
      queryFnForLoad={() => getUser(userId!)}
      onDataLoaded={(data) => {
        form.setValues(data);
        setPermissions(data.permissions);
      }}
      title={`Edit user`}
      onSubmit={form.onSubmit}
      onSave={() => updateUser(userId!, { ...form.values, permissions })}
      queryKeyForInvalidation={["users"]}
      disabledSaving={readOnly}
    >
      <UserEditor
        form={form}
        permissions={permissions}
        onChange={(perms) => {
          setPermissions(perms);
        }}
        readOnly={readOnly}
      />
    </ResourceEdition>
  );
}
