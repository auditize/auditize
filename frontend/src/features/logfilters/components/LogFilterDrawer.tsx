import { Drawer } from "@mantine/core";

import { LogFilterManagement } from "./LogFilterManagement";

export function LogFilterDrawer({
  opened,
  onClose,
}: {
  opened: boolean;
  onClose: () => void;
}) {
  return (
    <Drawer
      position="right"
      offset={8}
      radius="md"
      opened={opened}
      onClose={onClose}
    >
      <LogFilterManagement />
    </Drawer>
  );
}
