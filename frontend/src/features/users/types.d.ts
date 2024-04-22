type User = {
  id: string;
  firstName: string;
  lastName: string;
  email: string;
};

type UserUpdate = {
  firstName?: string;
  lastName?: string;
  email?: string;
};
