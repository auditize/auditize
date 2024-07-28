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
import { Notifications } from "@mantine/notifications";
import "@mantine/notifications/styles.css";
import { QueryClientProvider } from "@tanstack/react-query";
import i18n from "i18next";
import "mantine-datatable/styles.layer.css";
import { useEffect } from "react";
import { useTranslation } from "react-i18next";
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
import { LogNavigationStateProvider, Logs } from "@/features/logs";
import { ReposManagement } from "@/features/repos";
import { ResetPassword, Signup } from "@/features/signup";
import { UsersManagement } from "@/features/users";
import { theme } from "@/theme";

import { Navbar, NavbarItem, NavbarItemGroup } from "./components/Navbar";
import { ApikeysManagement } from "./features/apikeys";
import { logOut } from "./features/auth";
import { LogI18nProfileManagement } from "./features/logi18nprofiles";
import { UserSettings } from "./features/users";
import { I18nProvider } from "./i18n";
import "./layers.css";
import { interceptStatusCode } from "./utils/axios";
import { auditizeQueryClient } from "./utils/query";

function logoutConfirmationModal(onLogout: () => void) {
  const { t } = i18n;
  return () =>
    modals.openConfirmModal({
      title: t("logout.title"),
      children: <Text size="sm">{t("logout.confirm")}</Text>,
      labels: { confirm: t("common.confirm"), cancel: t("common.cancel") },
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
  const { t } = useTranslation();
  return (
    <>
      <Text size="sm">{t("logout.expiration")}</Text>
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
  const { t } = useTranslation();
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
          <Menu.Item onClick={() => open()}>
            {t("navigation.preferences")}
          </Menu.Item>
          <Menu.Item onClick={logoutConfirmationModal(declareLogout)}>
            {t("navigation.logout")}
          </Menu.Item>
        </Menu.Dropdown>
      </Menu>
      <UserSettings opened={opened} onClose={close} />
    </>
  );
}

function Main() {
  const { currentUser, declareLogout } = useAuthenticatedUser();
  const { t } = useTranslation();

  useEffect(() => {
    let alreadyIntercepted = false;

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
  }, []);

  return (
    <AppShell header={{ height: 55 }} padding="lg">
      <AppShell.Header bg="#fbfbfb">
        <Flex h="100%" px="lg" justify="space-between" align="center">
          <Navbar>
            <NavbarItem
              label={t("navigation.logs")}
              url="/logs"
              condition={currentUser.permissions.logs.read != "none"}
            />
            <NavbarItemGroup label={t("navigation.management")}>
              <NavbarItem
                label={t("navigation.repositories")}
                url="/repos"
                condition={currentUser.permissions.management.repos.read}
              />
              <NavbarItem
                label={t("navigation.logi18nprofiles")}
                url="/log-i18n-profiles"
                condition={currentUser.permissions.management.repos.read}
              />
              <NavbarItem
                label={t("navigation.users")}
                url="/users"
                condition={currentUser.permissions.management.users.read}
              />
              <NavbarItem
                label={t("navigation.apikeys")}
                url="/apikeys"
                condition={currentUser.permissions.management.apikeys.read}
              />
            </NavbarItemGroup>
          </Navbar>
          <Space w="6rem" />
          <UserMenu />
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
  const { isAuthenticated, declareLogin, currentUser } = useCurrentUser();

  const router = createBrowserRouter([
    isAuthenticated
      ? {
          path: "/",
          element: (
            <I18nProvider lang={currentUser!.lang}>
              <Main />
            </I18nProvider>
          ),
          children: [
            {
              path: "logs",
              element: (
                <LogNavigationStateProvider>
                  <Logs />
                </LogNavigationStateProvider>
              ),
            },
            {
              path: "repos",
              element: <ReposManagement />,
            },
            {
              path: "log-i18n-profiles",
              element: <LogI18nProfileManagement />,
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
      element: (
        <I18nProvider>
          <Signup />
        </I18nProvider>
      ),
    },
    {
      path: "/reset-password/:token",
      element: (
        <I18nProvider>
          <ResetPassword />
        </I18nProvider>
      ),
    },
    {
      path: "/login",
      element: (
        <I18nProvider>
          <LoginForm onLogin={declareLogin} />
        </I18nProvider>
      ),
    },
  ]);

  return <RouterProvider router={router} />;
}

export default function App() {
  return (
    <MantineProvider theme={theme}>
      <ModalsProvider modals={{ logout: LogoutModal }}>
        <Notifications />
        <QueryClientProvider client={auditizeQueryClient()}>
          <AuthProvider>
            <AppRoutes />
          </AuthProvider>
        </QueryClientProvider>
      </ModalsProvider>
    </MantineProvider>
  );
}
