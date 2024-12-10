import { useQuery } from "@tanstack/react-query";
import { createContext, useContext, useState } from "react";

import { CurrentUserInfo, getCurrentUserInfo } from "./api";

type AuthContextProps = {
  currentUser: CurrentUserInfo | null;
  declareLogin: (user: CurrentUserInfo) => void;
  declareLogout: () => void;
  updateUserInfo: (user: CurrentUserInfo) => void;
  isAuthenticated: boolean;
  isRefreshingAuthData: boolean;
};

const AuthContext = createContext<AuthContextProps | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [loggedIn, setLoggedIn] = useState<CurrentUserInfo | null>(null);
  const [loggedOut, setLoggedOut] = useState<boolean>(false);
  const authQuery = useQuery({
    queryKey: ["/users/me"],
    // FIXME: handle possible errors and make a distinction between 401 and others
    queryFn: () => getCurrentUserInfo(),
    staleTime: Infinity,
    enabled: !loggedIn && !loggedOut,
  });

  const currentUser = loggedOut ? null : loggedIn || authQuery.data || null;

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
        updateUserInfo: (user: CurrentUserInfo) => {
          setLoggedIn(user);
        },
        isAuthenticated: currentUser !== null,
        isRefreshingAuthData: authQuery.isFetching,
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

export function useAuthenticatedUser(): {
  currentUser: CurrentUserInfo;
  declareLogout: () => void;
  updateUserInfo: (user: CurrentUserInfo) => void;
} {
  const { currentUser, declareLogout, updateUserInfo } = useCurrentUser();
  if (!currentUser) {
    throw new Error("User is not authenticated");
  }
  return { currentUser, declareLogout, updateUserInfo };
}
