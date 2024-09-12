import i18n from "i18next";
import { useTranslation } from "react-i18next";

import { Permissions } from "../types";

function formatRwPermissions(
  label: string,
  { read, write }: { read?: boolean; write?: boolean },
): string | null {
  if (!read && !write) {
    return null;
  }
  const { t } = i18n;

  const value =
    read && write
      ? t("permission.summary.readwrite")
      : read
        ? t("permission.summary.read")
        : t("permission.summary.write");
  return `${label} (${value})`;
}

export function PermissionSummary({
  permissions,
}: {
  permissions: Permissions;
}) {
  const { t } = useTranslation();
  const p = permissions;

  if (p.isSuperadmin) {
    return <b>{t("permission.summary.superadmin")} 💪</b>;
  }

  const lst = [];

  if (p.logs.read || p.logs.write) {
    lst.push(formatRwPermissions(t("permission.logs"), p.logs));
  } else if (p.logs.repos.length > 0) {
    lst.push(
      t("permission.logs") + " (" + t("permission.summary.partial") + ")",
    );
  }

  lst.push(
    formatRwPermissions(t("permission.repositories"), p.management.repos),
  );
  lst.push(formatRwPermissions(t("permission.users"), p.management.users));
  lst.push(formatRwPermissions(t("permission.apikeys"), p.management.apikeys));

  return lst.filter(Boolean).join(", ") || undefined;
}
