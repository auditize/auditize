import { Tabs } from "@mantine/core";
import { useTranslation } from "react-i18next";

import { Permissions } from "../types";
import { PermissionManagement } from "./PermissionManagement";

export function WithPermissionManagement({
  permissions,
  onChange,
  children,
  readOnly = false,
}: {
  permissions: Permissions;
  onChange: (permissions: Permissions) => void;
  children: React.ReactNode;
  readOnly?: boolean;
}) {
  const { t } = useTranslation();
  return (
    <Tabs defaultValue="general">
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
