type Apikey = {
  id?: string;
  name: string;
  permissions: Auditize.Permissions;
};

type ApikeyUpdate = {
  name?: string;
  permissions?: Auditize.Permissions;
};
