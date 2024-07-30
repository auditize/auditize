import {
  Anchor,
  Button,
  Center,
  LoadingOverlay,
  Modal,
  Stack,
  TextInput,
  Title,
} from "@mantine/core";
import { isEmail, useForm } from "@mantine/form";
import { useDisclosure, useDocumentTitle } from "@mantine/hooks";
import { useMutation } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Navigate, useNavigate, useSearchParams } from "react-router-dom";

import { InlineErrorMessage } from "@/components/InlineErrorMessage";
import Message from "@/components/Message";
import { ModalActionButtons } from "@/components/ModalActionButtons";
import { ModalTitle } from "@/components/ModalTitle";

import { CurrentUserInfo, forgotPassword, logIn } from "../api";
import { useCurrentUser } from "../contexts";

function getDefaultPageForUser(
  user: CurrentUserInfo,
  searchParams: URLSearchParams,
): string {
  if (searchParams.get("redirect")) {
    return decodeURIComponent(searchParams.get("redirect")!);
  }
  if (user.permissions.logs.read !== "none") {
    return "/logs";
  }
  if (user.permissions.management.users.read) {
    return "/users";
  }
  if (user.permissions.management.apikeys.read) {
    return "/apikeys";
  }
  if (user.permissions.management.repos.read) {
    return "/repos";
  }
  return "/";
}

function ForgotPassword({
  opened,
  onClose,
}: {
  opened: boolean;
  onClose: () => void;
}) {
  const { t } = useTranslation();
  const form = useForm({
    initialValues: {
      email: "",
    },

    validate: {
      email: isEmail(t("login.form.email.invalid")),
    },
  });
  const mutation = useMutation({
    mutationFn: forgotPassword,
  });

  useEffect(() => {
    if (!opened) {
      form.reset();
      mutation.reset();
    }
  }, [opened]);

  return (
    <Modal
      opened={opened}
      onClose={onClose}
      title={<ModalTitle>{t("forgotPassword.title")}</ModalTitle>}
    >
      <form onSubmit={form.onSubmit((values) => mutation.mutate(values.email))}>
        <Stack>
          <LoadingOverlay visible={mutation.isPending} />
          <Message.Info>{t("forgotPassword.description")}</Message.Info>
          <TextInput
            {...form.getInputProps("email")}
            key={form.key("email")}
            placeholder={t("login.form.email.placeholder")}
            disabled={mutation.isSuccess}
            data-autofocus
          />
          <InlineErrorMessage>
            {mutation.error ? mutation.error.message : null}
          </InlineErrorMessage>
          {mutation.isSuccess && (
            <Message.Success>{t("forgotPassword.emailSent")}</Message.Success>
          )}
          <ModalActionButtons
            validateButtonLabel={t("common.send")}
            onClose={onClose}
            closeOnly={mutation.isSuccess}
          />
        </Stack>
      </form>
    </Modal>
  );
}

export function LoginForm({
  onLogin,
}: {
  onLogin: (user: CurrentUserInfo) => void;
}) {
  const { t } = useTranslation();
  const { currentUser } = useCurrentUser();
  const [searchParams] = useSearchParams();
  const form = useForm({
    mode: "uncontrolled",
    initialValues: {
      email: "",
      password: "",
    },

    validate: {
      email: isEmail(t("login.form.email.invalid")),
    },
  });
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const mutation = useMutation({
    mutationFn: (values: { email: string; password: string }) =>
      logIn(values.email, values.password),
    onSuccess: (user) => {
      onLogin(user);
      navigate(getDefaultPageForUser(user, searchParams), { replace: true });
    },
    onError: (error) => {
      setError(error.message);
    },
  });
  const [
    forgotPasswordOpened,
    { open: openForgotPassword, close: closeForgotPassword },
  ] = useDisclosure();
  useDocumentTitle(t("login.title"));

  if (currentUser) {
    return (
      <Navigate to={getDefaultPageForUser(currentUser, searchParams)} replace />
    );
  }

  return (
    <>
      <form onSubmit={form.onSubmit((values) => mutation.mutate(values))}>
        <Center pt="4rem">
          <Stack align="center">
            <Title order={1}>{t("login.welcome")}</Title>
            <Stack pt="1rem" gap="1.25rem">
              <TextInput
                {...form.getInputProps("email")}
                key={form.key("email")}
                label={t("login.form.email.label")}
                placeholder={t("login.form.email.placeholder")}
              />
              <TextInput
                {...form.getInputProps("password")}
                key={form.key("password")}
                label={t("login.form.password.label")}
                placeholder={t("login.form.password.placeholder")}
                type="password"
              />
              <Button type="submit">{t("login.signIn")}</Button>
              <InlineErrorMessage>{error}</InlineErrorMessage>
            </Stack>
            <Anchor onClick={openForgotPassword} size="sm">
              {"(" + t("forgotPassword.link") + ")"}
            </Anchor>
          </Stack>
        </Center>
      </form>
      <ForgotPassword
        opened={forgotPasswordOpened}
        onClose={closeForgotPassword}
      />
    </>
  );
}
