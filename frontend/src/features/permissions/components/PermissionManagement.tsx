import { Checkbox, Group, Stack, Table } from "@mantine/core";
import { useQuery } from "@tanstack/react-query";

import { Section } from "@/components/Section";
import { useAuthenticatedUser } from "@/features/auth";
import { getAllMyRepos } from "@/features/repos";

import {
  ApplicablePermissions,
  Permissions,
  ReadWritePermissions,
} from "../types";

function ReadWritePermissionManagement({
  perms,
  onChange,
  assignablePerms,
  readOnly = false,
}: {
  perms: ReadWritePermissions;
  onChange: (perms: ReadWritePermissions) => void;
  assignablePerms: ReadWritePermissions;
  readOnly?: boolean;
}) {
  return (
    <Group>
      <Checkbox
        label="Read"
        checked={perms.read}
        onChange={(event) =>
          onChange({ ...perms, read: event.currentTarget.checked })
        }
        disabled={readOnly || !assignablePerms.read}
      />
      <Checkbox
        label="Write"
        checked={perms.write}
        onChange={(event) =>
          onChange({ ...perms, write: event.currentTarget.checked })
        }
        disabled={readOnly || !assignablePerms.write}
      />
    </Group>
  );
}

function EntityPermissionManagement({
  name,
  perms,
  onChange,
  assignablePerms,
  readOnly = false,
}: {
  name: string;
  perms: ReadWritePermissions;
  onChange: (perms: ReadWritePermissions) => void;
  assignablePerms: ReadWritePermissions;
  readOnly?: boolean;
}) {
  return (
    <Table.Tr>
      <Table.Td width="35%">{name}</Table.Td>
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

function ManagementPermissionManagement({
  perms,
  onChange,
  assignablePerms,
  readOnly = false,
}: {
  perms: Permissions["management"];
  onChange: (perms: Permissions["management"]) => void;
  assignablePerms: Permissions["management"];
  readOnly?: boolean;
}) {
  return (
    <Section title="Management">
      <Table withRowBorders={false}>
        <Table.Tbody>
          <EntityPermissionManagement
            name="Repositories"
            perms={perms.repos}
            onChange={(repoPerms) => onChange({ ...perms, repos: repoPerms })}
            assignablePerms={assignablePerms.repos}
            readOnly={readOnly}
          />
          <EntityPermissionManagement
            name="Users"
            perms={perms.users}
            onChange={(userPerms) => onChange({ ...perms, users: userPerms })}
            assignablePerms={assignablePerms.users}
            readOnly={readOnly}
          />
          <EntityPermissionManagement
            name="API keys"
            perms={perms.apikeys}
            onChange={(apikeyPerms) =>
              onChange({ ...perms, apikeys: apikeyPerms })
            }
            assignablePerms={assignablePerms.apikeys}
            readOnly={readOnly}
          />
        </Table.Tbody>
      </Table>
    </Section>
  );
}

function LogsPermissionManagement({
  perms,
  onChange,
  assignablePerms,
  readOnly = false,
}: {
  perms: Permissions["logs"];
  onChange: (perms: Permissions["logs"]) => void;
  assignablePerms: ApplicablePermissions["logs"];
  readOnly?: boolean;
}) {
  // NB: silent loading and error handling here
  const { data } = useQuery({
    queryKey: ["assignable-log-repos"],
    queryFn: () => getAllMyRepos({}),
    placeholderData: [],
  });

  // Convert the array of repo permissions to an object for easier handling
  const repoPerms = Object.fromEntries(
    perms.repos.map((repoPerms) => [
      repoPerms.repoId,
      { read: repoPerms.read, write: repoPerms.write },
    ]),
  ) as Record<string, ReadWritePermissions>;

  // Convert back the "repoPerm" object to an array to fit the expected type
  const normalizeRepoPerms = (
    permsObject: Record<string, ReadWritePermissions>,
  ) =>
    Object.entries(permsObject).map(([repoId, perms]) => ({
      repoId,
      ...perms,
    }));

  return (
    <>
      <Section title="Logs">
        <Table withRowBorders={false}>
          <Table.Tbody>
            <Table.Tr>
              <Table.Td width="35%">
                <b>All repositories</b>
              </Table.Td>
              <Table.Td>
                <ReadWritePermissionManagement
                  perms={perms}
                  assignablePerms={{
                    read: assignablePerms.read === "all",
                    write: assignablePerms.write === "all",
                  }}
                  onChange={(logPerms) => onChange({ ...perms, ...logPerms })}
                  readOnly={readOnly}
                />
              </Table.Td>
            </Table.Tr>
            {data?.map((assignableRepo) => (
              <Table.Tr key={assignableRepo.id}>
                <Table.Td>{assignableRepo.name}</Table.Td>
                <Table.Td>
                  <ReadWritePermissionManagement
                    perms={
                      repoPerms[assignableRepo.id] || {
                        read: false,
                        write: false,
                      }
                    }
                    assignablePerms={{
                      read: perms.read
                        ? false
                        : assignablePerms.read === "all" ||
                          assignableRepo.permissions.readLogs,
                      write: perms.write
                        ? false
                        : assignablePerms.write === "all" ||
                          assignableRepo.permissions.writeLogs,
                    }}
                    onChange={(repoLogsPerms) =>
                      onChange({
                        ...perms,
                        repos: normalizeRepoPerms({
                          ...repoPerms,
                          [assignableRepo.id]: repoLogsPerms,
                        }),
                      })
                    }
                    readOnly={readOnly}
                  />
                </Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
      </Section>
    </>
  );
}

export function PermissionManagement({
  perms,
  onChange,
  readOnly = false,
}: {
  perms: Permissions;
  onChange: (perms: Permissions) => void;
  readOnly?: boolean;
}) {
  const { currentUser } = useAuthenticatedUser();
  const assignablePerms = currentUser.permissions;

  return (
    <Stack pt="xs">
      <Checkbox
        label="Superadmin (grant all permissions)"
        checked={perms.isSuperadmin}
        onChange={(event) =>
          onChange({
            ...perms,
            isSuperadmin: event.currentTarget.checked,
          })
        }
        disabled={readOnly || !assignablePerms.isSuperadmin}
        pl="xs"
      />
      <ManagementPermissionManagement
        perms={perms.management}
        assignablePerms={assignablePerms.management}
        onChange={(managementPerms) =>
          onChange({ ...perms, management: managementPerms })
        }
        readOnly={readOnly || perms.isSuperadmin}
      />
      <LogsPermissionManagement
        perms={perms.logs}
        assignablePerms={assignablePerms.logs}
        onChange={(logsPerms) => onChange({ ...perms, logs: logsPerms })}
        readOnly={readOnly || perms.isSuperadmin}
      />
    </Stack>
  );
}
