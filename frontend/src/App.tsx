import '@mantine/core/styles.css';
import '@mantine/dates/styles.css';
import { MantineProvider, AppShell, Group, UnstyledButton } from '@mantine/core';
import { theme } from './theme';
import { Logs } from './features/logs';
import { ReposManagement } from './features/repos';
import {
  QueryClient,
  QueryClientProvider,
} from '@tanstack/react-query'
import {
  createBrowserRouter,
  RouterProvider,
  Route,
  Link,
  Outlet
} from "react-router-dom";

function Main() {
  return (
    <AppShell header={{height: 60}}>
      <AppShell.Header>
        <Group h="100%" px="md" justify="right">
          <Group ml="xl">
            <UnstyledButton>
              <Link to="/logs">Logs</Link>
            </UnstyledButton>
            <UnstyledButton>
              <Link to="/repos">Repositories Management</Link>
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
  const queryClient = new QueryClient();

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
        }
      ]
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
