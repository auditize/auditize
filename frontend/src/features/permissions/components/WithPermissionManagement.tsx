import { Tabs } from "@mantine/core";
import { useTranslation } from "react-i18next";

import { Permissions } from "../types";
import { PermissionManagement } from "./PermissionManagement";

export type PermissionManagementTab = "general" | "permissions" | null;

export function WithPermissionManagement({
  selectedTab,
  onTabChange,
  permissions,
  onChange,
  children,
  readOnly = false,
}: {
  selectedTab: PermissionManagementTab;
  onTabChange: (tab: PermissionManagementTab) => void;
  permissions: Permissions;
  onChange: (permissions: Permissions) => void;
  children: React.ReactNode;
  readOnly?: boolean;
}) {
  const { t } = useTranslation();
  return (
    <Tabs
      value={selectedTab}
      onChange={onTabChange as (tab: string | null) => void}
    >
      <Tabs.List>
        <Tabs.Tab value="general">{t("permission.tab.general")}</Tabs.Tab>
        <Tabs.Tab value="permissions">
          {t("permission.tab.permissions")}
        </Tabs.Tab>
      </Tabs.List>

      <Tabs.Panel value="general" pt="sm">
        {children}
      </Tabs.Panel>
      <Tabs.Panel value="permissions" pt="sm">
        <PermissionManagement
          perms={permissions}
          onChange={onChange}
          readOnly={readOnly}
        />
      </Tabs.Panel>
    </Tabs>
  );
}
