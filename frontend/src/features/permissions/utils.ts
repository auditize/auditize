import { Permissions } from "./types";

export function emptyPermissions(): Permissions {
  return {
    isSuperadmin: false,
    logs: {
      read: false,
      write: false,
      repos: [],
    },
    management: {
      repos: {
        read: false,
        write: false,
      },
      users: {
        read: false,
        write: false,
      },
      apikeys: {
        read: false,
        write: false,
      },
    },
  };
}
