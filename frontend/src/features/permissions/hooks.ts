import { useQuery } from "@tanstack/react-query";

import { useAuthenticatedUser } from "../auth";
import { getAllMyRepos } from "../repo";
import { Permissions } from "./types";

export function usePermissionsNormalizer() {
  const { currentUser } = useAuthenticatedUser();
  const assignableReposQuery = useQuery({
    queryKey: ["repos", "available-for-permissions"],
    queryFn: () => getAllMyRepos({}),
  });
  const assignablePerms = currentUser.permissions;

  return (perms: Permissions) => ({
    isSuperadmin: assignablePerms.isSuperadmin ? perms.isSuperadmin : undefined,
    management: {
      repos: {
        read: assignablePerms.management.repos.read
          ? perms.management.repos.read
          : undefined,
        write: assignablePerms.management.repos.write
          ? perms.management.repos.write
          : undefined,
      },
      users: {
        read: assignablePerms.management.users.read
          ? perms.management.users.read
          : undefined,
        write: assignablePerms.management.users.write
          ? perms.management.users.write
          : undefined,
      },
      apikeys: {
        read: assignablePerms.management.apikeys.read
          ? perms.management.apikeys.read
          : undefined,
        write: assignablePerms.management.apikeys.write
          ? perms.management.apikeys.write
          : undefined,
      },
    },
    logs: {
      read: assignablePerms.logs.read === "all" ? perms.logs.read : undefined,
      write:
        assignablePerms.logs.write === "all" ? perms.logs.write : undefined,
      repos: perms.logs.repos
        .map((repoPerms) => {
          const assignableRepo = (assignableReposQuery.data ?? []).find(
            (repo) => repo.id === repoPerms.repoId,
          );
          return {
            repoId: repoPerms.repoId,
            read: assignableRepo?.permissions.read ? repoPerms.read : undefined,
            write: assignableRepo?.permissions.write
              ? repoPerms.write
              : undefined,
            readableNodes: repoPerms.readableNodes,
          };
        })
        .filter(
          (repoPerms) =>
            repoPerms.read !== undefined || repoPerms.write !== undefined,
        ),
    },
  });
}
