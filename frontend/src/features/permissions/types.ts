export interface ReadWritePermissions {
  read?: boolean;
  write?: boolean;
}

export interface RepoLogPermissions extends ReadWritePermissions {
  repoId: string;
  readableEntities: Array<string>;
}

export interface Permissions {
  isSuperadmin?: boolean;
  logs: {
    read?: boolean;
    write?: boolean;
    repos: Array<RepoLogPermissions>;
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
