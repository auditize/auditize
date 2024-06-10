import {
  Box,
  Button,
  Group,
  LoadingOverlay,
  Modal,
  Select,
  Stack,
  Tabs,
} from "@mantine/core";
import { useForm } from "@mantine/form";
import { useMutation } from "@tanstack/react-query";

import { CustomModalTitle } from "@/components/CustomModalTitle";
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
    <Box px="lg">
      <LoadingOverlay visible={mutation.isPending} />
      <form onSubmit={form.onSubmit(() => mutation.mutate())}>
        <Stack>
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
  return (
    <Modal
      title={<CustomModalTitle>User Settings</CustomModalTitle>}
      opened={opened}
      onClose={onClose}
    >
      <Tabs defaultValue="general" orientation="vertical">
        <Tabs.List>
          <Tabs.Tab value="general">General</Tabs.Tab>
        </Tabs.List>
        <Tabs.Panel value="general">
          <GeneralSettings onClose={onClose} />
        </Tabs.Panel>
      </Tabs>
    </Modal>
  );
}
