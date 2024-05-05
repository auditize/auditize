import { useAuthenticatedUser } from "@/features/auth";
import { getAllMyRepos } from "@/features/repos";
import { Accordion, Checkbox, Group, Table } from "@mantine/core";
import { useQuery } from "@tanstack/react-query";

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

function EntitiesPermissionManagement(
  {
    perms,
    onChange,
    assignablePerms,
    readOnly = false,
  }: 
  {
    perms: Auditize.Permissions['entities'],
    onChange: (perms: Auditize.Permissions['entities']) => void,
    assignablePerms: Auditize.Permissions['entities']
    readOnly?: boolean
  }
) {
  return (
    <Accordion.Item value="entities">
      <Accordion.Control>Entities</Accordion.Control>
        <Accordion.Panel>
          <Table withRowBorders={false}>
            <Table.Tbody>
              <EntityPermissionManagement
                name="Repositories"
                perms={perms.repos}
                onChange={(repoPerms) => onChange({...perms, repos: repoPerms})}
                assignablePerms={assignablePerms.repos}
                readOnly={readOnly}
              />
              <EntityPermissionManagement
                name="Users"
                perms={perms.users}
                onChange={(userPerms) => onChange({...perms, users: userPerms})}
                assignablePerms={assignablePerms.users}
                readOnly={readOnly}
              />
              <EntityPermissionManagement
                name="Integrations"
                perms={perms.integrations}
                onChange={(intgrPerms) => onChange({...perms, integrations: intgrPerms})}
                assignablePerms={assignablePerms.integrations}
                readOnly={readOnly}
              />
            </Table.Tbody>
          </Table>
        </Accordion.Panel>
      </Accordion.Item>
  );
}

function LogsPermissionManagement(
  {
    perms,
    onChange,
    assignablePerms,
    readOnly = false,
  }: 
  {
    perms: Auditize.Permissions['logs'],
    onChange: (perms: Auditize.Permissions['logs']) => void,
    assignablePerms: Auditize.ReadWritePermissions
    readOnly?: boolean
  }
) {
  const {data, error, isPending} = useQuery({
    queryKey: ['assignable-log-repos'],
    queryFn: () => getAllMyRepos({}),
    placeholderData: [],
  });

  return (
    <Accordion.Item value="logs">
      <Accordion.Control>Logs</Accordion.Control>
        <Accordion.Panel>
          <Table withRowBorders={false}>
            <Table.Tbody>
              <Table.Tr>
                <Table.Td><b>All repositories</b></Table.Td>
                <Table.Td>
                  <ReadWritePermissionManagement
                    perms={perms}
                    assignablePerms={assignablePerms}
                    onChange={(logPerms) => onChange({...perms, ...logPerms})}
                    readOnly={readOnly}
                  />
                </Table.Td>
              </Table.Tr>
              {
                data!.map((assignableRepo) => (
                  <Table.Tr key={assignableRepo.id}>
                    <Table.Td>{assignableRepo.name}</Table.Td>
                    <Table.Td>
                      <ReadWritePermissionManagement
                        perms={perms.repos[assignableRepo.id] || {read: false, write: false}}
                        assignablePerms={{
                          read: perms.read ? false : (assignablePerms.read || assignableRepo.permissions.read_logs),
                          write: perms.write ? false : (assignablePerms.write || assignableRepo.permissions.write_logs),
                        }}
                        onChange={
                          (repoLogsPerms) => onChange({...perms, repos: {...perms.repos, [assignableRepo.id]: repoLogsPerms}})
                        }
                        readOnly={readOnly}
                      />
                    </Table.Td>
                  </Table.Tr>
                ))
              }
            </Table.Tbody>
          </Table>
        </Accordion.Panel>
      </Accordion.Item>
  );
}

export function PermissionManagement(
  {perms, onChange, readOnly = false}: 
  {perms: Auditize.Permissions, onChange: (perms: Auditize.Permissions) => void, readOnly?: boolean}
) {
  const {currentUser} = useAuthenticatedUser();
  const assignablePerms = currentUser.permissions;

  return (
    <div>
      <Checkbox
        label="Superadmin"
        checked={perms.isSuperadmin}
        onChange={(event) => onChange({...perms, isSuperadmin: event.currentTarget.checked})}
        disabled={readOnly || !assignablePerms.isSuperadmin}
      />
      <Accordion multiple defaultValue={['entities', 'logs']}>
        <EntitiesPermissionManagement
          perms={perms.entities}
          assignablePerms={assignablePerms.entities}
          onChange={(entitiesPerms) => onChange({...perms, entities: entitiesPerms})}
          readOnly={readOnly || perms.isSuperadmin}
        />
        <LogsPermissionManagement
          perms={perms.logs}
          assignablePerms={assignablePerms.logs}
          onChange={(logsPerms) => onChange({...perms, logs: logsPerms})}
          readOnly={readOnly || perms.isSuperadmin}
        />
      </Accordion>
    </div>
  );
}