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
    management: {
      repos: ReadWritePermissions;
      users: ReadWritePermissions;
      apikeys: ReadWritePermissions;
    };
  }

  type ApplicableLogPermissionScope = "all" | "partial" | "none";

  export interface ApplicablePermissions {
    isSuperadmin: boolean;
    logs: {
      read: ApplicableLogPermissionScope;
      write: ApplicableLogPermissionScope;
    };
    management: {
      repos: ReadWritePermissions;
      users: ReadWritePermissions;
      apikeys: ReadWritePermissions;
    };
  }
}
