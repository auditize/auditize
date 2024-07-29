import {
  Box,
  Button,
  Group,
  LoadingOverlay,
  Modal,
  PasswordInput,
  Select,
  Stack,
  Tabs,
} from "@mantine/core";
import { isNotEmpty, matchesField, useForm } from "@mantine/form";
import { useMutation } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { InlineErrorMessage } from "@/components/InlineErrorMessage";
import { ModalTitle } from "@/components/ModalTitle";
import { useAuthenticatedUser } from "@/features/auth";

import { updateUserMe } from "../api";

function PasswordChange({ onClose }: { onClose: () => void }) {
  const { t } = useTranslation();
  const form = useForm({
    mode: "uncontrolled",
    initialValues: {
      password: "",
      passwordConfirmation: "",
    },
    validate: {
      password: isNotEmpty(t("accountSettings.form.password.required")),
      passwordConfirmation: matchesField(
        "password",
        t("accountSettings.form.passwordConfirmation.doesNotMatch"),
      ),
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
        <Stack>
          <PasswordInput
            {...form.getInputProps("password")}
            label={t("accountSettings.form.password.label")}
            placeholder={t("accountSettings.form.password.placeholder")}
            key={form.key("password")}
          />
          <PasswordInput
            {...form.getInputProps("passwordConfirmation")}
            label={t("accountSettings.form.passwordConfirmation.label")}
            placeholder={t(
              "accountSettings.form.passwordConfirmation.placeholder",
            )}
            key={form.key("passwordConfirmation")}
          />
          <Group>
            <Button onClick={onClose}>{t("common.cancel")}</Button>
            <Button type="submit" color="blue">
              {t("common.save")}
            </Button>
          </Group>
          <InlineErrorMessage>
            {mutation.error ? mutation.error.message : null}
          </InlineErrorMessage>
        </Stack>
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
        <Stack>
          <Select
            label={t("user.form.language.label")}
            data={[
              { value: "en", label: t("language.en") },
              { value: "fr", label: t("language.fr") },
            ]}
            allowDeselect={false}
            {...form.getInputProps("lang")}
          />
          <Group>
            <Button onClick={onClose}>{t("common.cancel")}</Button>
            <Button type="submit" color="blue">
              {t("common.save")}
            </Button>
          </Group>
        </Stack>
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
