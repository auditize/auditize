import { Tabs } from '@mantine/core';

export function WithPermissionManagement({children}: {children: React.ReactNode}) {
  return (
    <Tabs defaultValue="general">
      <Tabs.List>
        <Tabs.Tab value="general">
          General
        </Tabs.Tab>
        <Tabs.Tab value="permissions">
          Permissions
        </Tabs.Tab>
      </Tabs.List>

      <Tabs.Panel value="general">
        {children}
      </Tabs.Panel>
      <Tabs.Panel value="permissions">
        PERMISSIONS !!!!
      </Tabs.Panel>
    </Tabs>
  );
}