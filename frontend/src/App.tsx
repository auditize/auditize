import {
  AppShell,
  Avatar,
  Button,
  Group,
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
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  createBrowserRouter,
  Navigate,
  NavLink,
  Outlet,
  RouterProvider,
  useLocation,
} from "react-router-dom";

import {
  AuthProvider,
  getUserHomeRoute,
  LoginForm,
  useAuthenticatedUser,
  useCurrentUser,
} from "@/features/auth";
import { LogNavigationStateProvider, Logs } from "@/features/log";
import { AccountSetup, PasswordReset } from "@/features/password-setup";
import { RepoManagement } from "@/features/repo";
import { UsersManagement } from "@/features/user";
import { theme } from "@/theme";

import "./App.css";
import logoPath from "./assets/logo.svg";
import { ModalTitle } from "./components/ModalTitle";
import { Navbar, NavbarItem, NavbarItemGroup } from "./components/Navbar";
import { ApikeysManagement } from "./features/apikey";
import { logOut } from "./features/auth";
import { About } from "./features/info";
import { LogI18nProfileManagement } from "./features/log-i18n-profile";
import { UserSettings } from "./features/user";
import { I18nProvider } from "./i18n";
import "./layers.css";
import { interceptStatusCode } from "./utils/axios";
import { auditizeQueryClient } from "./utils/query";

function logoutConfirmationModal(onLogout: () => void) {
  const { t } = i18n;
  return () =>
    modals.openConfirmModal({
      title: <ModalTitle>{t("logout.title")}</ModalTitle>,
      children: <Text size="sm">{t("logout.confirm")}</Text>,
      labels: { confirm: t("common.confirm"), cancel: t("common.cancel") },
      onConfirm: async () => {
        await logOut();
        onLogout();
      },
      groupProps: { justify: "center" },
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
  const [prefsOpened, setPrefsOpened] = useState(false);
  const [aboutOpened, setAboutOpened] = useState(false);
  const initials =
    currentUser.firstName[0].toUpperCase() +
    currentUser.lastName[0].toUpperCase();

  return (
    <>
      <Menu shadow="md">
        <Menu.Target>
          <UnstyledButton>
            <Avatar>{initials}</Avatar>
          </UnstyledButton>
        </Menu.Target>
        <Menu.Dropdown>
          <Menu.Item onClick={() => setAboutOpened(true)}>
            {t("navigation.about")}
          </Menu.Item>
          <Menu.Item onClick={() => setPrefsOpened(true)}>
            {t("navigation.preferences")}
          </Menu.Item>
          <Menu.Divider />
          <Menu.Item onClick={logoutConfirmationModal(declareLogout)}>
            {t("navigation.logout")}
          </Menu.Item>
        </Menu.Dropdown>
      </Menu>
      <UserSettings
        opened={prefsOpened}
        onClose={() => setPrefsOpened(false)}
      />
      <About opened={aboutOpened} onClose={() => setAboutOpened(false)} />
    </>
  );
}

function Logo({}) {
  const { currentUser } = useAuthenticatedUser();

  return (
    <NavLink to={getUserHomeRoute(currentUser)}>
      <img
        src={logoPath}
        alt="Auditize"
        height={25}
        style={{ display: "block" }} // for image vertical alignment
      />
    </NavLink>
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
      <AppShell.Header bg="var(--auditize-header-color)">
        <Group h="100%" px="lg" justify="space-between" align="center">
          <Group>
            <Logo />
            <Navbar>
              <NavbarItem
                label={t("navigation.logs")}
                url="/logs"
                condition={currentUser.permissions.logs.read != "none"}
              />
              <NavbarItemGroup label={t("navigation.management")}>
                <NavbarItemGroup.Entry
                  label={t("navigation.repositories")}
                  url="/repos"
                  condition={currentUser.permissions.management.repos.read}
                />
                <NavbarItemGroup.Entry
                  label={t("navigation.logi18nprofiles")}
                  url="/log-i18n-profiles"
                  condition={currentUser.permissions.management.repos.read}
                />
                <NavbarItemGroup.Entry
                  label={t("navigation.users")}
                  url="/users"
                  condition={currentUser.permissions.management.users.read}
                />
                <NavbarItemGroup.Entry
                  label={t("navigation.apikeys")}
                  url="/apikeys"
                  condition={currentUser.permissions.management.apikeys.read}
                />
              </NavbarItemGroup>
            </Navbar>
          </Group>
          <Space w="6rem" />
          <UserMenu />
        </Group>
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
              element: <RepoManagement />,
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
      path: "/account-setup/:token",
      element: (
        <I18nProvider>
          <AccountSetup />
        </I18nProvider>
      ),
    },
    {
      path: "/password-reset/:token",
      element: (
        <I18nProvider>
          <PasswordReset />
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
