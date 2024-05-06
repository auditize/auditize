export function emptyPermissions(): Auditize.Permissions {
  return {
    isSuperadmin: false,
    logs: {
      read: false,
      write: false,
      repos: {},
    },
    entities: {
      repos: {
        read: false,
        write: false,
      },
      users: {
        read: false,
        write: false,
      },
      integrations: {
        read: false,
        write: false,
      },
    },
  };
}
