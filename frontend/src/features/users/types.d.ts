type User = {
  id?: string;
  firstName: string;
  lastName: string;
  email: string;
  permissions: Auditize.Permissions;
};

type UserUpdate = {
  firstName?: string;
  lastName?: string;
  email?: string;
  permissions?: Auditize.Permissions;
};
