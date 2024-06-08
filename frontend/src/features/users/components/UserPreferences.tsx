import {
  Box,
  Button,
  Group,
  LoadingOverlay,
  Modal,
  Select,
  Tabs,
} from "@mantine/core";
import { useForm } from "@mantine/form";
import { useMutation } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { useAuthenticatedUser } from "@/features/auth";

import { updateUserMe } from "../api";

function GeneralSettings({ onClose }: { onClose: () => void }) {
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
    },
  });

  return (
    <Box p="lg">
      <LoadingOverlay visible={mutation.isPending} />
      <form onSubmit={form.onSubmit(() => mutation.mutate())}>
        <Select
          label="Language"
          placeholder="Select language"
          data={[
            { value: "en", label: "English" },
            { value: "fr", label: "Français" },
          ]}
          allowDeselect={false}
          {...form.getInputProps("lang")}
        />
        <Group>
          <Button onClick={onClose}>Cancel</Button>
          <Button type="submit" color="blue">
            Save
          </Button>
        </Group>
      </form>
    </Box>
  );
}

export function UserSettings({ opened: opened }: { opened: boolean }) {
  const navigate = useNavigate();
  const handleClose = () => navigate(-1);

  return (
    <Modal opened={opened} onClose={handleClose}>
      <Tabs defaultValue="general" orientation="vertical">
        <Tabs.List>
          <Tabs.Tab value="general">General</Tabs.Tab>
        </Tabs.List>
        <Tabs.Panel value="general">
          <GeneralSettings onClose={handleClose} />
        </Tabs.Panel>
      </Tabs>
    </Modal>
  );
}
