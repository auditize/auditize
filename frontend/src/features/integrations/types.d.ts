type Integration = {
  id?: string;
  name: string;
  permissions: Auditize.Permissions;
};

type IntegrationUpdate = {
  name?: string;
  permissions?: Auditize.Permissions;
};
