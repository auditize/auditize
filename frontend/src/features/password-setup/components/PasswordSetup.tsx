import {
  Alert,
  Anchor,
  Button,
  Center,
  PasswordInput,
  Stack,
  TextInput,
  Title,
} from "@mantine/core";
import { useForm } from "@mantine/form";
import { IconExclamationCircle } from "@tabler/icons-react";
import { useMutation, useQuery } from "@tanstack/react-query";
import React, { useEffect } from "react";
import { Trans, useTranslation } from "react-i18next";
import { NavLink, useParams } from "react-router-dom";

import {
  ApiErrorMessage,
  useApiErrorMessageBuilder,
} from "@/components/ErrorMessage";
import Message from "@/components/Message";
import { usePasswordValidation } from "@/components/PasswordForm";
import { useI18nContext } from "@/i18n";

import { getPasswordResetInfo, setPassword } from "../api";
import { useDocumentTitle } from "@mantine/hooks";

function usePasswordSetupForm() {
  const passwordValidators = usePasswordValidation();
  return useForm({
    mode: "uncontrolled",
    initialValues: {
      firstName: "",
      lastName: "",
      email: "",
      password: "",
      passwordConfirmation: "",
    },
    validate: {
      ...passwordValidators,
    },
  });
}

function PasswordSetup({
  title,
  successMessage,
}: {
  title: string;
  successMessage: React.ReactNode;
}) {
  const { t } = useTranslation();
  const { lang } = useI18nContext();
  const apiErrorMessageBuilder = useApiErrorMessageBuilder();
  const { token } = useParams();
  const form = usePasswordSetupForm();
  const query = useQuery({
    queryKey: ["passwordReset", token],
    queryFn: () => getPasswordResetInfo(token!, lang),
  });
  const mutation = useMutation({
    mutationFn: (password: string) => setPassword(token!, password, lang),
  });
  useDocumentTitle(t("passwordSetup.documentTitle"));

  useEffect(() => {
    if (query.data) {
      form.setValues(query.data);
    }
  }, [query.data]);

  if (query.error) {
    return (
      <Center pt="4rem">
        <Alert
          title={t("common.error.error")}
          icon={<IconExclamationCircle />}
          color="red"
          variant="light"
        >
          {apiErrorMessageBuilder(query.error, { raw: true })}
        </Alert>
      </Center>
    );
  }

  const disabledForm =
    query.isLoading || mutation.isPending || mutation.isSuccess;

  return (
    <Center>
      <Stack align="center">
        <Title order={1} pt="xl">
          {title}
        </Title>
        <form
          onSubmit={form.onSubmit((values) => mutation.mutate(values.password))}
        >
          <Stack w="25rem" p="1rem">
            <TextInput
              {...form.getInputProps("firstName")}
              label={t("passwordSetup.form.firstName.label")}
              key={form.key("firstName")}
              disabled
            />
            <TextInput
              {...form.getInputProps("lastName")}
              label={t("passwordSetup.form.lastName.label")}
              key={form.key("lastName")}
              disabled
            />
            <TextInput
              {...form.getInputProps("email")}
              key={form.key("email")}
              label={t("passwordSetup.form.email.label")}
              disabled
            />
            <PasswordInput
              {...form.getInputProps("password")}
              label={t("common.passwordForm.password.label")}
              placeholder={t("common.passwordForm.password.placeholder")}
              key={form.key("password")}
              disabled={disabledForm}
            />
            <PasswordInput
              {...form.getInputProps("passwordConfirmation")}
              label={t("common.passwordForm.passwordConfirmation.label")}
              placeholder={t(
                "common.passwordForm.passwordConfirmation.placeholder",
              )}
              key={form.key("passwordConfirmation")}
              disabled={disabledForm}
            />
            <Button type="submit" disabled={disabledForm}>
              {t("common.submit")}
            </Button>
            <ApiErrorMessage error={mutation.error} />
          </Stack>
        </form>

        {mutation.isSuccess && (
          <Message.Success>
            <>
              {successMessage} <br />
              <Trans i18nKey="passwordSetup.loginLink">
                You can now log in by&nbsp;
                <Anchor component={NavLink} to="/login">
                  clicking on this link
                </Anchor>
                .
              </Trans>
            </>
          </Message.Success>
        )}
      </Stack>
    </Center>
  );
}

export function AccountSetup() {
  const { t } = useTranslation();
  return (
    <PasswordSetup
      title={t("passwordSetup.accountSetup.title")}
      successMessage={t("passwordSetup.accountSetup.success")}
    />
  );
}

export function PasswordReset() {
  const { t } = useTranslation();
  return (
    <PasswordSetup
      title={t("passwordSetup.passwordReset.title")}
      successMessage={t("passwordSetup.passwordReset.success")}
    />
  );
}
