import {
  AppShell,
  Button,
  Group,
  MantineProvider,
  Space,
  Text,
  Tooltip,
} from "@mantine/core";
import "@mantine/core/styles.css";
import "@mantine/dates/styles.css";
import { ContextModalProps, modals, ModalsProvider } from "@mantine/modals";
import { IconLogout } from "@tabler/icons-react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useEffect } from "react";
import { createBrowserRouter, Outlet, RouterProvider } from "react-router-dom";

import { AuthProvider, LogInForm, useCurrentUser } from "@/features/auth";
import { Logs } from "@/features/logs";
import { ReposManagement } from "@/features/repos";
import { Signup } from "@/features/signup";
import { UsersManagement } from "@/features/users";
import { theme } from "@/theme";

import { Navbar, NavbarItem, NavbarItemGroup } from "./components/Navbar";
import { ApikeysManagement } from "./features/apikeys";
import { logOut } from "./features/auth";
import { interceptStatusCode } from "./utils/axios";

function logoutConfirmationModal(notifyLoggedOut: () => void) {
  return () =>
    modals.openConfirmModal({
      title: "Please confirm log-out",
      children: <Text size="sm">Do you really want to log out?</Text>,
      labels: { confirm: "Confirm", cancel: "Cancel" },
      onConfirm: async () => {
        await logOut();
        notifyLoggedOut();
      },
    });
}

function LoggedOutModal({
  context,
  id,
  innerProps,
}: ContextModalProps<{ notifyLoggedOut: () => void }>) {
  return (
    <>
      <Text size="sm">Your session has expired, you need to log-in again.</Text>
      <Button
        fullWidth
        mt="md"
        onClick={() => {
          innerProps.notifyLoggedOut();
          context.closeModal(id);
        }}
      >
        Ok
      </Button>
    </>
  );
}

function Main() {
  const { currentUser, notifyLoggedOut } = useCurrentUser();

  useEffect(() => {
    let alreadyIntercepted = false;

    if (currentUser !== null) {
      const interceptorUnmount = interceptStatusCode(401, () => {
        if (!alreadyIntercepted) {
          alreadyIntercepted = true; // avoid multiple modals in a row when we have multiple 401 responses
          modals.openContextModal({
            modal: "loggedOut",
            innerProps: { notifyLoggedOut },
          });
        }
      });
      return interceptorUnmount;
    }
  }, [currentUser]);

  return (
    <AppShell header={{ height: 60 }}>
      <AppShell.Header>
        <Group h="100%" px="6rem" justify="space-between">
          <Navbar>
            <NavbarItem label="Log-in" url="/log-in" condition={!currentUser} />
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
          <Tooltip label="Log-out">
            <div style={{ cursor: "pointer" }}>
              <IconLogout
                onClick={logoutConfirmationModal(notifyLoggedOut)}
                size={"1.3rem"}
              />
            </div>
          </Tooltip>
        </Group>
      </AppShell.Header>
      <AppShell.Main>
        <Outlet />
      </AppShell.Main>
    </AppShell>
  );
}

function AppRoutes() {
  const { isAuthenticated, refreshUser } = useCurrentUser();

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
          element: <Main />,
        },
    {
      path: "/signup/:token",
      element: <Signup />,
    },
    {
      path: "/log-in",
      element: <LogInForm onLogged={refreshUser} />,
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
      },
    },
  });

  return (
    <MantineProvider theme={theme}>
      <ModalsProvider modals={{ loggedOut: LoggedOutModal }}>
        <QueryClientProvider client={queryClient}>
          <AuthProvider>
            <AppRoutes />
          </AuthProvider>
        </QueryClientProvider>
      </ModalsProvider>
    </MantineProvider>
  );
}
