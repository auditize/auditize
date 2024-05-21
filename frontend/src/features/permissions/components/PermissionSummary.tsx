import { Permissions } from "../types";

function formatRwPermissions(
  label: string,
  { read, write }: { read: boolean; write: boolean },
): string | null {
  if (!read && !write) {
    return null;
  }

  const value = read && write ? "rw" : read ? "read" : "write";
  return `${label} (${value})`;
}

export function PermissionSummary({
  permissions,
}: {
  permissions: Permissions;
}) {
  const p = permissions;

  if (p.isSuperadmin) {
    return <b>Superadmin 💪</b>;
  }

  const lst = [];

  if (p.logs.read || p.logs.write) {
    lst.push(formatRwPermissions("Logs", p.logs));
  } else if (p.logs.repos.length > 0) {
    lst.push("Logs (partial)");
  }

  lst.push(formatRwPermissions("Repositories", p.management.repos));
  lst.push(formatRwPermissions("Users", p.management.users));
  lst.push(formatRwPermissions("API Keys", p.management.apikeys));

  return lst.filter(Boolean).join(", ") || <i>None</i>;
}
