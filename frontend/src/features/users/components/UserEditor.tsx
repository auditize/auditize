import { Select, Stack, TextInput } from "@mantine/core";
import { isEmail, isNotEmpty, useForm, UseFormReturnType } from "@mantine/form";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

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
  const { t } = useTranslation();
  return useForm({
    initialValues: {
      firstName: "",
      lastName: "",
      email: "",
      lang: "en",
      ...values,
    },
    validate: {
      firstName: isNotEmpty(t("user.form.firstName.required")),
      lastName: isNotEmpty(t("user.form.lastName.required")),
      email: isEmail(t("user.form.email.required")),
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
  const { t } = useTranslation();
  return (
    <WithPermissionManagement
      permissions={permissions}
      onChange={onChange}
      readOnly={readOnly}
    >
      <Stack gap={"sm"}>
        <TextInput
          label={t("user.form.firstName.label")}
          placeholder={t("user.form.firstName.placeholder")}
          data-autofocus
          {...form.getInputProps("firstName")}
          disabled={readOnly}
        />
        <TextInput
          label={t("user.form.lastName.label")}
          placeholder={t("user.form.lastName.placeholder")}
          data-autofocus
          {...form.getInputProps("lastName")}
          disabled={readOnly}
        />
        <TextInput
          label={t("user.form.email.label")}
          placeholder={t("user.form.email.placeholder")}
          data-autofocus
          {...form.getInputProps("email")}
          disabled={readOnly}
        />
        <Select
          label={t("user.form.language.label")}
          data={[
            { value: "en", label: t("language.en") },
            { value: "fr", label: t("language.fr") },
          ]}
          allowDeselect={false}
          {...form.getInputProps("lang")}
          disabled={readOnly}
        />
      </Stack>
    </WithPermissionManagement>
  );
}

export function UserCreation({
  opened,
  onClose,
}: {
  opened?: boolean;
  onClose: () => void;
}) {
  const form = useUserForm({});
  const [permissions, setPermissions] = useState<Permissions>(() =>
    emptyPermissions(),
  );
  const { t } = useTranslation();

  useEffect(() => {
    form.reset();
    setPermissions(emptyPermissions());
  }, [opened]);

  return (
    <ResourceCreation
      title={t("user.create.title")}
      opened={!!opened}
      onClose={onClose}
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
  onClose,
  readOnly,
}: {
  userId: string | null;
  onClose: () => void;
  readOnly: boolean;
}) {
  const { t } = useTranslation();
  const form = useUserForm({});
  const [permissions, setPermissions] = useState<Permissions>(() =>
    emptyPermissions(),
  );

  return (
    <ResourceEdition
      resourceId={userId}
      onClose={onClose}
      queryKeyForLoad={["user", userId]}
      queryFnForLoad={() => getUser(userId!)}
      onDataLoaded={(data) => {
        const { firstName, lastName, email, lang } = data;
        form.setValues({ firstName, lastName, email, lang });
        setPermissions(data.permissions);
      }}
      title={t("user.edit.title")}
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
