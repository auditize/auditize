type CurrentUserInfo = {
  id: string;
  firstName: string;
  lastName: string;
  email: string;
  permissions: {
    isSuperadmin: boolean;
    logs: {
      read: boolean;
      write: boolean;
    };
    entities: {
      repos: {read: boolean; write: boolean};
      users: {read: boolean; write: boolean};
      integrations: {read: boolean; write: boolean};
    };
  };
};
