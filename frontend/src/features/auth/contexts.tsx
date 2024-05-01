import { useQuery } from "@tanstack/react-query";
import { createContext, useContext } from "react";
import { getLoggedInUser } from "./api";

type AuthContextProps = {
  currentUser: CurrentUserInfo | null;
};

const AuthContext = createContext<AuthContextProps | null>(null);

export function AuthProvider({children}: {children: React.ReactNode}) {
  const { data } = useQuery({
    queryKey: ['current-user'],
    // FIXME: handle possible errors and make a distinction between 401 and others
    queryFn: () => getLoggedInUser(),
    staleTime: Infinity
  });

  return (
    <AuthContext.Provider value={{currentUser: data || null}}>
      {children}
    </AuthContext.Provider>
  );
}

export function useCurrentUser() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useCurrentUser must be used within an AuthProvider');
  }
  return context;
}