import { useQuery } from "@tanstack/react-query";
import { createContext, useContext, useState } from "react";

import { CurrentUserInfo, getCurrentUserInfo } from "./api";

type AuthContextProps = {
  currentUser: CurrentUserInfo | null;
  declareLogin: (user: CurrentUserInfo) => void;
  declareLogout: () => void;
  isAuthenticated: boolean;
  isRefreshingAuthData: boolean;
};

const AuthContext = createContext<AuthContextProps | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [loggedIn, setLoggedIn] = useState<CurrentUserInfo | null>(null);
  const [loggedOut, setLoggedOut] = useState<boolean>(false);
  const { data: defaultAuthData, isPending } = useQuery({
    queryKey: ["/users/me"],
    // FIXME: handle possible errors and make a distinction between 401 and others
    queryFn: () => getCurrentUserInfo(),
    staleTime: Infinity,
  });

  const currentUser = loggedOut ? null : loggedIn || defaultAuthData || null;

  return (
    <AuthContext.Provider
      value={{
        currentUser: currentUser,
        declareLogin: (user: CurrentUserInfo) => {
          setLoggedIn(user);
          setLoggedOut(false);
        },
        declareLogout: () => {
          setLoggedIn(null);
          setLoggedOut(true);
        },
        isAuthenticated: currentUser !== null,
        isRefreshingAuthData: isPending,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useCurrentUser(): AuthContextProps {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useCurrentUser must be used within an AuthProvider");
  }
  return context;
}

export function useAuthenticatedUser(): { currentUser: CurrentUserInfo } {
  const { currentUser } = useCurrentUser();
  if (!currentUser) {
    throw new Error("User is not authenticated");
  }
  return { currentUser };
}
