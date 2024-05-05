import { useQuery } from "@tanstack/react-query";
import { createContext, useContext, useState } from "react";
import { getCurrentUserInfo } from "./api";

type AuthContextProps = {
  currentUser: CurrentUserInfo | null;
  refreshUser: () => void;
  isAuthenticated: boolean;
};

const AuthContext = createContext<AuthContextProps | null>(null);

export function AuthProvider({children}: {children: React.ReactNode}) {
  const [lastRefresh, setLastRefresh] = useState<Date>(() => new Date());
  const { data } = useQuery({
    queryKey: ['current-user', lastRefresh],
    // FIXME: handle possible errors and make a distinction between 401 and others
    queryFn: () => getCurrentUserInfo(),
    staleTime: Infinity
  });

  return (
    <AuthContext.Provider value={{
      currentUser: data || null,
      refreshUser: () => setLastRefresh(new Date()),
      isAuthenticated: !!data,
    }}>
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

export function useAuthenticatedUser() {
  const {currentUser} = useCurrentUser();
  if (!currentUser) {
    throw new Error('User is not authenticated');
  }
  return {currentUser};
}
