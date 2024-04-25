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
  Outlet
} from "react-router-dom";
import { LogInForm } from '@/features/log-in';

function Main() {
  return (
    <AppShell header={{height: 60}}>
      <AppShell.Header>
        <Group h="100%" px="md" justify="right">
          <Group ml="xl">
          <UnstyledButton>
              <Link to="/log-in">Log-in</Link>
            </UnstyledButton>
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
          </Group>
        </Group>
      </AppShell.Header>
      <AppShell.Main>
        <Outlet />
      </AppShell.Main>
    </AppShell>
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

  const router = createBrowserRouter([
    {
      path: "/",
      element: <Main/>,
      children: [
        {
          path: "logs",
          element: <Logs/>
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
    },
    {
      path: "/signup/:token",
      element: <Signup/>
    },
    {
      path: "/log-in",
      element: <LogInForm/>
    }
  ]);

  return (
    <MantineProvider theme={theme}>
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router}/>
      </QueryClientProvider>
    </MantineProvider>
  );
}
