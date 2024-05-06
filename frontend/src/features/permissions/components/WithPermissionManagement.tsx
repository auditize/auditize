import { Tabs } from "@mantine/core";

import { PermissionManagement } from "./PermissionManagement";

export function WithPermissionManagement({
  permissions,
  onChange,
  children,
  readOnly = false,
}: {
  permissions: Auditize.Permissions;
  onChange: (permissions: Auditize.Permissions) => void;
  children: React.ReactNode;
  readOnly?: boolean;
}) {
  return (
    <Tabs defaultValue="general">
      <Tabs.List>
        <Tabs.Tab value="general">General</Tabs.Tab>
        <Tabs.Tab value="permissions">Permissions</Tabs.Tab>
      </Tabs.List>

      <Tabs.Panel value="general">{children}</Tabs.Panel>
      <Tabs.Panel value="permissions">
        <PermissionManagement
          perms={permissions}
          onChange={onChange}
          readOnly={readOnly}
        />
      </Tabs.Panel>
    </Tabs>
  );
}
