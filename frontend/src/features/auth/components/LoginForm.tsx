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
import { AxiosError } from "axios";
import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { Navigate, useNavigate, useSearchParams } from "react-router-dom";

import { ApiErrorMessage, ErrorMessage } from "@/components/ErrorMessage";
import Message from "@/components/Message";
import { ModalActionButtons } from "@/components/ModalActionButtons";
import { ModalTitle } from "@/components/ModalTitle";
import { useI18nContext } from "@/i18n";

import { CurrentUserInfo, forgotPassword, logIn } from "../api";
import { useCurrentUser } from "../contexts";
import { getUserHomeRoute } from "../utils";

function getPostLoginRoute(
  user: CurrentUserInfo,
  searchParams: URLSearchParams,
): string {
  if (searchParams.get("redirect")) {
    const redirect = decodeURIComponent(searchParams.get("redirect")!);
    if (redirect && redirect !== "/") {
      return redirect;
    }
  }
  return getUserHomeRoute(user);
}

function ForgotPassword({
  opened,
  onClose,
}: {
  opened: boolean;
  onClose: () => void;
}) {
  const { t } = useTranslation();
  const { lang } = useI18nContext();
  const form = useForm({
    initialValues: {
      email: "",
    },

    validate: {
      email: isEmail(t("login.form.email.invalid")),
    },
  });
  const mutation = useMutation({
    mutationFn: (email: string) => forgotPassword(email, lang),
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
          <ApiErrorMessage error={mutation.error} />
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

function LoginErrorMessage({ error }: { error: Error | null }) {
  const { t } = useTranslation();
  if (error instanceof AxiosError && error.response?.status === 401) {
    return <ErrorMessage message={t("login.invalidCredentials")} />;
  } else {
    return <ApiErrorMessage error={error} />;
  }
}

export function LoginForm({
  onLogin,
}: {
  onLogin: (user: CurrentUserInfo) => void;
}) {
  const { t } = useTranslation();
  const { lang } = useI18nContext();
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
  const navigate = useNavigate();
  const mutation = useMutation({
    mutationFn: (values: { email: string; password: string }) =>
      logIn(values.email, values.password, lang),
    onSuccess: (user) => {
      onLogin(user);
      navigate(getPostLoginRoute(user, searchParams), { replace: true });
    },
  });
  const [
    forgotPasswordOpened,
    { open: openForgotPassword, close: closeForgotPassword },
  ] = useDisclosure();
  useDocumentTitle(t("login.title"));

  if (currentUser) {
    return (
      <Navigate to={getPostLoginRoute(currentUser, searchParams)} replace />
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
            </Stack>
            <LoginErrorMessage error={mutation.error} />
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
