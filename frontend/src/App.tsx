import {
  AppShell,
  Button,
  Group,
  MantineProvider,
  Text,
  UnstyledButton,
} from "@mantine/core";
import "@mantine/core/styles.css";
import "@mantine/dates/styles.css";
import { ContextModalProps, modals, ModalsProvider } from "@mantine/modals";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useEffect } from "react";
import {
  createBrowserRouter,
  Link,
  Outlet,
  RouterProvider,
} from "react-router-dom";

import { AuthProvider, LogInForm, useCurrentUser } from "@/features/auth";
import { Logs } from "@/features/logs";
import { ReposManagement } from "@/features/repos";
import { Signup } from "@/features/signup";
import { UsersManagement } from "@/features/users";
import { theme } from "@/theme";

import { VisibleIf } from "./components/VisibleIf";
import { logOut } from "./features/auth";
import { IntegrationsManagement } from "./features/integrations";
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
        <Group h="100%" px="md" justify="right">
          <Group ml="xl">
            <VisibleIf condition={!currentUser}>
              <UnstyledButton>
                <Link to="/log-in">Log-in</Link>
              </UnstyledButton>
            </VisibleIf>
            <VisibleIf condition={!!currentUser}>
              <UnstyledButton
                onClick={logoutConfirmationModal(notifyLoggedOut)}
              >
                Log-out
              </UnstyledButton>
            </VisibleIf>
            <VisibleIf condition={!!currentUser}>
              {" "}
              {/* FIXME: actual check depends on https://nde.atlassian.net/browse/ADZ-179 */}
              <UnstyledButton>
                <Link to="/logs">Logs</Link>
              </UnstyledButton>
            </VisibleIf>
            <VisibleIf
              condition={
                currentUser && currentUser.permissions.entities.repos.read
              }
            >
              <UnstyledButton>
                <Link to="/repos">Repository Management</Link>
              </UnstyledButton>
            </VisibleIf>
            <VisibleIf
              condition={
                currentUser && currentUser.permissions.entities.users.read
              }
            >
              <UnstyledButton>
                <Link to="/users">User Management</Link>
              </UnstyledButton>
            </VisibleIf>
            <VisibleIf
              condition={
                currentUser &&
                currentUser.permissions.entities.integrations.read
              }
            >
              <UnstyledButton>
                <Link to="/integrations">Integration Management</Link>
              </UnstyledButton>
            </VisibleIf>
          </Group>
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
              path: "integrations",
              element: <IntegrationsManagement />,
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
