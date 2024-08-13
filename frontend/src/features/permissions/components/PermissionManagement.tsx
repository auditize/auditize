import { Checkbox, Group, Stack, Table } from "@mantine/core";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { Section } from "@/components/Section";
import { useAuthenticatedUser } from "@/features/auth";
import { MultiNodeSelectorPicker } from "@/features/log";
import { getAllMyRepos } from "@/features/repo";

import {
  ApplicablePermissions,
  Permissions,
  ReadWritePermissions,
  RepoLogPermissions,
} from "../types";

type ReadWritePermissionManagementProps = {
  perms: ReadWritePermissions;
  onChange: (perms: ReadWritePermissions) => void;
  assignablePerms: ReadWritePermissions;
  readOnly?: boolean;
};

function BaseReadWritePermissionManagement({
  perms,
  onChange,
  assignablePerms,
  readOnly = false,
}: ReadWritePermissionManagementProps) {
  const { t } = useTranslation();
  return (
    <>
      <Checkbox
        label={t("permission.read")}
        checked={perms.read}
        onChange={(event) =>
          onChange({ ...perms, read: event.currentTarget.checked })
        }
        disabled={readOnly || !assignablePerms.read}
      />
      <Checkbox
        label={t("permission.write")}
        checked={perms.write}
        onChange={(event) =>
          onChange({ ...perms, write: event.currentTarget.checked })
        }
        disabled={readOnly || !assignablePerms.write}
      />
    </>
  );
}

function ReadWritePermissionManagement(
  props: ReadWritePermissionManagementProps,
) {
  const { t } = useTranslation();
  return (
    <Group>
      <BaseReadWritePermissionManagement {...props} />
    </Group>
  );
}

function LogRepoPermissionManagement({
  perms,
  onChange,
  assignablePerms,
  readOnly = false,
}: {
  perms: RepoLogPermissions;
  onChange: (perms: RepoLogPermissions) => void;
  assignablePerms: ReadWritePermissions;
  readOnly?: boolean;
}) {
  return (
    <Group>
      <BaseReadWritePermissionManagement
        perms={perms}
        onChange={(values) => onChange({ ...perms, ...values })}
        assignablePerms={assignablePerms}
        readOnly={readOnly}
      />
      <MultiNodeSelectorPicker
        repoId={perms.repoId}
        nodeRefs={perms.readableNodes}
        onChange={(nodes) => onChange({ ...perms, readableNodes: nodes })}
        disabled={readOnly || !assignablePerms.read || !perms.read}
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
  const { t } = useTranslation();
  return (
    <Section title={t("permission.management")}>
      <Table withRowBorders={false}>
        <Table.Tbody>
          <EntityPermissionManagement
            name={t("permission.repositories")}
            perms={perms.repos}
            onChange={(repoPerms) => onChange({ ...perms, repos: repoPerms })}
            assignablePerms={assignablePerms.repos}
            readOnly={readOnly}
          />
          <EntityPermissionManagement
            name={t("permission.users")}
            perms={perms.users}
            onChange={(userPerms) => onChange({ ...perms, users: userPerms })}
            assignablePerms={assignablePerms.users}
            readOnly={readOnly}
          />
          <EntityPermissionManagement
            name={t("permission.apikeys")}
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
  const { t } = useTranslation();

  // NB: silent loading and error handling here
  const reposQuery = useQuery({
    queryKey: ["repos", "available-for-permissions"],
    queryFn: () => getAllMyRepos({}),
    placeholderData: [],
  });

  // Convert the array of repo permissions to an object for easier handling
  const repoPerms = Object.fromEntries(
    perms.repos.map((repoPerms) => [repoPerms.repoId, repoPerms]),
  ) as Record<string, RepoLogPermissions>;

  return (
    <>
      <Section title={t("permission.logs")}>
        <Table withRowBorders={false}>
          <Table.Tbody>
            <Table.Tr>
              <Table.Td width="35%">
                <b>{t("permission.allRepos")}</b>
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
            {reposQuery.data?.map((assignableRepo) => (
              <Table.Tr key={assignableRepo.id}>
                <Table.Td>{assignableRepo.name}</Table.Td>
                <Table.Td>
                  <LogRepoPermissionManagement
                    perms={
                      repoPerms[assignableRepo.id] || {
                        repoId: assignableRepo.id,
                        read: false,
                        write: false,
                        readableNodes: [],
                      }
                    }
                    assignablePerms={{
                      read: perms.read
                        ? false
                        : assignablePerms.read === "all" ||
                          (assignableRepo.permissions.read &&
                            assignableRepo.permissions.readableNodes.length ===
                              0),
                      write: perms.write
                        ? false
                        : assignablePerms.write === "all" ||
                          assignableRepo.permissions.write,
                    }}
                    onChange={(repoLogsPerms) =>
                      onChange({
                        ...perms,
                        repos: Object.entries({
                          ...repoPerms,
                          [assignableRepo.id]: repoLogsPerms,
                        }).map(([_, perms]) => perms),
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
  const { t } = useTranslation();
  const { currentUser } = useAuthenticatedUser();
  const assignablePerms = currentUser.permissions;

  return (
    <Stack pt="xs">
      <Checkbox
        label={t("permission.superadmin")}
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
