import {
  Box,
  Flex,
  LoadingOverlay,
  Modal,
  PasswordInput,
  rem,
  Select,
  Space,
  Stack,
  Tabs,
} from "@mantine/core";
import { useForm } from "@mantine/form";
import { useMutation } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { ApiErrorMessage } from "@/components/ErrorMessage";
import { ModalActionButtons } from "@/components/ModalActionButtons";
import { ModalTitle } from "@/components/ModalTitle";
import { usePasswordValidation } from "@/components/PasswordForm";
import { useAuthenticatedUser } from "@/features/auth";

import { updateUserMe } from "../api";

function PasswordChange({ onClose }: { onClose: () => void }) {
  const { t } = useTranslation();
  const passwordValidators = usePasswordValidation();
  const form = useForm({
    mode: "uncontrolled",
    initialValues: {
      password: "",
      passwordConfirmation: "",
    },
    validate: {
      ...passwordValidators,
    },
  });
  const mutation = useMutation({
    mutationFn: () => {
      const { password } = form.getValues();
      return updateUserMe({ password });
    },
    onSuccess: () => onClose(),
  });

  return (
    <Box px="lg">
      <LoadingOverlay visible={mutation.isPending} />
      <form onSubmit={form.onSubmit(() => mutation.mutate())}>
        <Stack gap="sm">
          <PasswordInput
            {...form.getInputProps("password")}
            label={t("common.passwordForm.password.label")}
            placeholder={t("common.passwordForm.password.placeholder")}
            key={form.key("password")}
          />
          <PasswordInput
            {...form.getInputProps("passwordConfirmation")}
            label={t("common.passwordForm.passwordConfirmation.label")}
            placeholder={t(
              "common.passwordForm.passwordConfirmation.placeholder",
            )}
            key={form.key("passwordConfirmation")}
          />
        </Stack>
        <Space h="xl" />
        <Flex justify="center" align="center">
          <ApiErrorMessage
            error={mutation.error}
            textProps={{ pt: "0", size: "sm" }}
          />
        </Flex>
        <ModalActionButtons
          validateButtonLabel={t("common.save")}
          onClose={onClose}
        />
      </form>
    </Box>
  );
}

function GeneralSettings({ onClose }: { onClose: () => void }) {
  const { t } = useTranslation();
  const { currentUser, updateUserInfo } = useAuthenticatedUser();
  const form = useForm({
    initialValues: {
      lang: currentUser.lang,
    },
    validate: {},
  });
  const mutation = useMutation({
    mutationFn: () => updateUserMe(form.values),
    onSuccess: (userInfo) => {
      updateUserInfo(userInfo);
      onClose();
    },
  });

  return (
    <Box px="lg">
      <LoadingOverlay visible={mutation.isPending} />
      <form onSubmit={form.onSubmit(() => mutation.mutate())}>
        <Stack gap="sm">
          <Select
            label={t("user.form.language.label")}
            data={[
              { value: "en", label: t("language.en") },
              { value: "fr", label: t("language.fr") },
            ]}
            allowDeselect={false}
            {...form.getInputProps("lang")}
            comboboxProps={{ shadow: "md" }}
          />
        </Stack>
        <Space h="xl" />
        <Flex justify="center" align="center">
          <ApiErrorMessage
            error={mutation.error}
            textProps={{ pt: "0", size: "sm" }}
          />
        </Flex>
        <ModalActionButtons
          validateButtonLabel={t("common.save")}
          onClose={onClose}
        />
      </form>
    </Box>
  );
}

export function UserSettings({
  opened: opened,
  onClose,
}: {
  opened: boolean;
  onClose: () => void;
}) {
  const { t } = useTranslation();
  return (
    <Modal
      title={<ModalTitle>{t("accountSettings.title")}</ModalTitle>}
      opened={opened}
      onClose={onClose}
      size={rem("500px")}
      padding="lg"
    >
      <Tabs defaultValue="general" orientation="vertical">
        <Tabs.List>
          <Tabs.Tab value="general">
            {t("accountSettings.tab.general")}
          </Tabs.Tab>
          <Tabs.Tab value="password">
            {t("accountSettings.tab.password")}
          </Tabs.Tab>
        </Tabs.List>
        <Tabs.Panel value="general">
          <GeneralSettings onClose={onClose} />
        </Tabs.Panel>
        <Tabs.Panel value="password">
          <PasswordChange onClose={onClose} />
        </Tabs.Panel>
      </Tabs>
    </Modal>
  );
}
