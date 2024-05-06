declare namespace Auditize {
  export interface ReadWritePermissions {
    read: boolean;
    write: boolean;
  }

  export interface Permissions {
    isSuperadmin: boolean;
    logs: {
      read: boolean;
      write: boolean;
      repos: Record<string, ReadWritePermissions>;
    };
    entities: {
      repos: ReadWritePermissions;
      users: ReadWritePermissions;
      integrations: ReadWritePermissions;
    };
  }
}
