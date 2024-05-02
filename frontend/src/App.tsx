import '@mantine/core/styles.css';
import '@mantine/dates/styles.css';
import { MantineProvider, AppShell, Group, UnstyledButton } from '@mantine/core';
import { theme } from '@/theme';
import { Logs } from '@/features/logs';
import { ReposManagement } from '@/features/repos';
import { UsersManagement } from '@/features/users';
import { IntegrationsManagement } from './features/integrations';
import { Signup } from '@/features/signup';
import {
  QueryClient,
  QueryClientProvider,
} from '@tanstack/react-query'
import {
  createBrowserRouter,
  RouterProvider,
  Link,
  Outlet,
} from "react-router-dom";
import { AuthProvider, LogInForm, useCurrentUser } from '@/features/auth';

function IfAuthenticated({isAuthenticated, children} : {isAuthenticated: boolean, children: React.ReactNode}) {
  return isAuthenticated ? <>{children}</> : null;
}

function IfAnonymous({isAuthenticated, children} : {isAuthenticated: boolean, children: React.ReactNode}) {
  return !isAuthenticated ? <>{children}</> : null;
}

function Main({isAuthenticated} : {isAuthenticated: boolean}) {
  return (
    <AppShell header={{height: 60}}>
      <AppShell.Header>
        <Group h="100%" px="md" justify="right">
          <Group ml="xl">
            <IfAnonymous isAuthenticated={isAuthenticated}>
              <UnstyledButton>
                <Link to="/log-in">Log-in</Link>
              </UnstyledButton>
            </IfAnonymous>
            <IfAuthenticated isAuthenticated={isAuthenticated}>
              <UnstyledButton>
                <Link to="/logs">Logs</Link>
              </UnstyledButton>
              <UnstyledButton>
                <Link to="/repos">Repository Management</Link>
              </UnstyledButton>
              <UnstyledButton>
                <Link to="/users">User Management</Link>
              </UnstyledButton>
              <UnstyledButton>
                <Link to="/integrations">Integration Management</Link>
              </UnstyledButton>
            </IfAuthenticated>
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
  const {isAuthenticated, refreshUser} = useCurrentUser();

  const router = createBrowserRouter([
    isAuthenticated ?
      {
        path: "/",
        element: <Main isAuthenticated={isAuthenticated}/>,
        children: [
          {
            path: "logs",
            element: <Logs/>,
          },
          {
            path: 'repos',
            element: <ReposManagement/>
          },
          {
            path: 'users',
            element: <UsersManagement/>
          },
          {
            path: 'integrations',
            element: <IntegrationsManagement/>
          }
        ],
      } :
      {
        path: "*",
        element: <Main isAuthenticated={isAuthenticated}/>,
      },
    {
      path: "/signup/:token",
      element: <Signup/>
    },
    {
      path: "/log-in",
      element: <LogInForm onLogged={refreshUser}/>
    }
  ]);

  return (
      <RouterProvider router={router}/>
  );
}

export default function App() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        refetchOnWindowFocus: false,
        retry: false
      }
    }
  });

  return (
    <MantineProvider theme={theme}>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </QueryClientProvider>
    </MantineProvider>
  );
}
