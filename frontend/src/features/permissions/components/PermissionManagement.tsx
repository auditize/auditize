import { useAuthenticatedUser, useCurrentUser } from "@/features/auth";
import { Checkbox } from "@mantine/core";

export function PermissionManagement(
  {permissions, onChange, readOnly = false}: 
  {permissions: Auditize.Permissions, onChange: (permissions: Auditize.Permissions) => void, readOnly?: boolean}
) {
  const {currentUser} = useAuthenticatedUser();
  const assignablePerms = currentUser.permissions;

  return (
    <div>
      <Checkbox
        label="Superadmin"
        checked={permissions.isSuperadmin}
        onChange={(event) => onChange({...permissions, isSuperadmin: event.currentTarget.checked})}
        disabled={readOnly || !assignablePerms.isSuperadmin}
      />
    </div>
  );
}