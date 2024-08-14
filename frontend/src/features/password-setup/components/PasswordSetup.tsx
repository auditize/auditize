import {
  Anchor,
  Button,
  Center,
  PasswordInput,
  Stack,
  TextInput,
  Title,
} from "@mantine/core";
import { useForm } from "@mantine/form";
import { useMutation, useQuery } from "@tanstack/react-query";
import { AxiosError } from "axios";
import React, { useEffect } from "react";
import { Trans, useTranslation } from "react-i18next";
import { NavLink, useParams } from "react-router-dom";

import { InlineErrorMessage } from "@/components/InlineErrorMessage";
import Message from "@/components/Message";
import { usePasswordValidation } from "@/components/PasswordForm";

import { getPasswordResetInfo, setPassword } from "../api";

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
  const { token } = useParams();
  const form = usePasswordSetupForm();
  const query = useQuery({
    queryKey: ["passwordReset", token],
    queryFn: () => getPasswordResetInfo(token!),
  });
  const mutation = useMutation({
    mutationFn: (password: string) => setPassword(token!, password),
  });

  useEffect(() => {
    if (query.data) {
      form.setValues(query.data);
    }
  }, [query.data]);

  if ((query?.error as AxiosError)?.response?.status === 404) {
    return (
      <Center>
        <h1>Invalid token</h1>
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
            <InlineErrorMessage>{mutation.error}</InlineErrorMessage>
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
