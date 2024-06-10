import {
  AppShell,
  Avatar,
  Button,
  Flex,
  MantineProvider,
  Menu,
  Space,
  Text,
  UnstyledButton,
} from "@mantine/core";
import "@mantine/core/styles.layer.css";
import "@mantine/dates/styles.layer.css";
import { useDisclosure } from "@mantine/hooks";
import { ContextModalProps, modals, ModalsProvider } from "@mantine/modals";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import "mantine-datatable/styles.layer.css";
import { useEffect } from "react";
import {
  createBrowserRouter,
  Navigate,
  Outlet,
  RouterProvider,
  useLocation,
} from "react-router-dom";

import {
  AuthProvider,
  LoginForm,
  useAuthenticatedUser,
  useCurrentUser,
} from "@/features/auth";
import { Logs } from "@/features/logs";
import { ReposManagement } from "@/features/repos";
import { Signup } from "@/features/signup";
import { UsersManagement } from "@/features/users";
import { theme } from "@/theme";

import { Navbar, NavbarItem, NavbarItemGroup } from "./components/Navbar";
import { ApikeysManagement } from "./features/apikeys";
import { logOut } from "./features/auth";
import { UserSettings } from "./features/users";
import "./layers.css";
import { interceptStatusCode } from "./utils/axios";

function logoutConfirmationModal(onLogout: () => void) {
  return () =>
    modals.openConfirmModal({
      title: "Please confirm logout",
      children: <Text size="sm">Do you really want to log out?</Text>,
      labels: { confirm: "Confirm", cancel: "Cancel" },
      onConfirm: async () => {
        await logOut();
        onLogout();
      },
    });
}

function LogoutModal({
  context,
  id,
  innerProps,
}: ContextModalProps<{ onLogout: () => void }>) {
  return (
    <>
      <Text size="sm">Your session has expired, you need to log in again.</Text>
      <Button
        fullWidth
        mt="md"
        onClick={() => {
          innerProps.onLogout();
          context.closeModal(id);
        }}
      >
        Ok
      </Button>
    </>
  );
}

function UserMenu() {
  const { currentUser, declareLogout } = useAuthenticatedUser();
  const [opened, { open, close }] = useDisclosure(false);
  const initials =
    currentUser.firstName[0].toUpperCase() +
    currentUser.lastName[0].toUpperCase();

  return (
    <>
      <Menu>
        <Menu.Target>
          <UnstyledButton>
            <Avatar>{initials}</Avatar>
          </UnstyledButton>
        </Menu.Target>
        <Menu.Dropdown>
          <Menu.Item onClick={() => open()}>Preferences</Menu.Item>
          <Menu.Item onClick={logoutConfirmationModal(declareLogout)}>
            Logout
          </Menu.Item>
        </Menu.Dropdown>
      </Menu>
      <UserSettings opened={opened} onClose={close} />
    </>
  );
}

function Main() {
  const { currentUser, declareLogout } = useCurrentUser();

  useEffect(() => {
    let alreadyIntercepted = false;

    if (currentUser !== null) {
      const interceptorUnmount = interceptStatusCode(401, () => {
        if (!alreadyIntercepted) {
          alreadyIntercepted = true; // avoid multiple modals in a row when we have multiple 401 responses
          modals.openContextModal({
            modal: "logout",
            innerProps: { onLogout: declareLogout },
          });
        }
      });
      return interceptorUnmount;
    }
  }, [currentUser]);

  return (
    <AppShell header={{ height: 55 }} padding="lg">
      <AppShell.Header bg="#fbfbfb">
        <Flex h="100%" px="lg" justify="space-between" align="center">
          <Navbar>
            <NavbarItem label="Login" url="/login" condition={!currentUser} />
            <NavbarItem
              label="Logs"
              url="/logs"
              condition={
                !!(currentUser && currentUser.permissions.logs.read != "none")
              }
            />
            <NavbarItemGroup label="Management">
              <NavbarItem
                label="Repositories"
                url="/repos"
                condition={
                  !!(
                    currentUser && currentUser.permissions.management.repos.read
                  )
                }
              />
              <NavbarItem
                label="Users"
                url="/users"
                condition={
                  !!(
                    currentUser && currentUser.permissions.management.users.read
                  )
                }
              />
              <NavbarItem
                label="API keys"
                url="/apikeys"
                condition={
                  !!(
                    currentUser &&
                    currentUser.permissions.management.apikeys.read
                  )
                }
              />
            </NavbarItemGroup>
          </Navbar>
          <Space w="6rem" />
          {currentUser && <UserMenu />}
        </Flex>
      </AppShell.Header>
      <AppShell.Main>
        <Outlet />
      </AppShell.Main>
    </AppShell>
  );
}

function CatchAll() {
  const { isRefreshingAuthData } = useCurrentUser();
  const location = useLocation();

  // Do not try to render or redirect anything until we know if the user
  // is authenticated or not to avoid flickering
  if (isRefreshingAuthData) {
    return null;
  }

  let path = "/login";
  if (location.pathname) {
    path +=
      "?redirect=" + encodeURIComponent(location.pathname + location.search);
  }

  return <Navigate to={path} replace />;
}

function AppRoutes() {
  const { isAuthenticated, declareLogin } = useCurrentUser();

  const router = createBrowserRouter([
    isAuthenticated
      ? {
          path: "/",
          element: <Main />,
          children: [
            {
              path: "logs",
              element: <Logs />,
            },
            {
              path: "repos",
              element: <ReposManagement />,
            },
            {
              path: "users",
              element: <UsersManagement />,
            },
            {
              path: "apikeys",
              element: <ApikeysManagement />,
            },
          ],
        }
      : {
          path: "*",
          element: <CatchAll />,
        },
    {
      path: "/signup/:token",
      element: <Signup />,
    },
    {
      path: "/login",
      element: <LoginForm onLogin={declareLogin} />,
    },
  ]);

  return <RouterProvider router={router} />;
}

export default function App() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        refetchOnWindowFocus: false,
        retry: false,
        staleTime: Infinity,
      },
    },
  });

  return (
    <MantineProvider theme={theme}>
      <ModalsProvider modals={{ logout: LogoutModal }}>
        <QueryClientProvider client={queryClient}>
          <AuthProvider>
            <AppRoutes />
          </AuthProvider>
        </QueryClientProvider>
      </ModalsProvider>
    </MantineProvider>
  );
}
