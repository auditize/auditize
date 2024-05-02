import { useAuthenticatedUser, useCurrentUser } from "@/features/auth";
import { Accordion, Checkbox, Group, Radio, Table } from "@mantine/core";

function ReadWritePermissionManagement(
  {
    perms,
    onChange,
    assignablePerms,
    readOnly = false,
  }: 
  {
    perms: Auditize.ReadWritePermissions,
    onChange: (perms: Auditize.ReadWritePermissions) => void,
    assignablePerms: Auditize.ReadWritePermissions
    readOnly?: boolean
  }
) {
  return (
    <Group>
      <Checkbox
        label="Read"
        checked={perms.read}
        onChange={(event) => onChange({...perms, read: event.currentTarget.checked})}
        disabled={readOnly || !assignablePerms.read}
      />
      <Checkbox
        label="Write"
        checked={perms.write}
        onChange={(event) => onChange({...perms, write: event.currentTarget.checked})}
        disabled={readOnly || !assignablePerms.write}
      />
    </Group>
  );
}

function EntityPermissionManagement(
  {
    name,
    perms,
    onChange,
    assignablePerms,
    readOnly = false,
  }: 
  {
    name: string,
    perms: Auditize.ReadWritePermissions,
    onChange: (perms: Auditize.ReadWritePermissions) => void,
    assignablePerms: Auditize.ReadWritePermissions
    readOnly?: boolean
  }
) {
  return (
    <Table.Tr>
      <Table.Td>{name}</Table.Td>
      <Table.Td>
        <ReadWritePermissionManagement
          perms={perms}
          onChange={onChange}
          assignablePerms={assignablePerms}
          readOnly={readOnly}
        />
      </Table.Td>
    </Table.Tr>
  );
}

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
      <Accordion multiple defaultValue={['entities']}>
        <Accordion.Item value="entities">
          <Accordion.Control>Entities</Accordion.Control>
          <Accordion.Panel>
            <Table withRowBorders={false}>
              <Table.Tbody>
                <EntityPermissionManagement
                  name="Repositories"
                  perms={permissions.entities.repos}
                  onChange={(perms) => onChange({...permissions, entities: {...permissions.entities, repos: perms}})}
                  assignablePerms={assignablePerms.entities.repos}
                  readOnly={readOnly}
                />
                <EntityPermissionManagement
                  name="Users"
                  perms={permissions.entities.users}
                  onChange={(perms) => onChange({...permissions, entities: {...permissions.entities, users: perms}})}
                  assignablePerms={assignablePerms.entities.users}
                  readOnly={readOnly}
                />
                <EntityPermissionManagement
                  name="Integrations"
                  perms={permissions.entities.integrations}
                  onChange={(perms) => onChange({...permissions, entities: {...permissions.entities, integrations: perms}})}
                  assignablePerms={assignablePerms.entities.integrations}
                  readOnly={readOnly}
                />
              </Table.Tbody>
            </Table>
          </Accordion.Panel>
        </Accordion.Item>
      </Accordion>
    </div>
  );
}