import '@mantine/core/styles.css';
import '@mantine/dates/styles.css';
import { MantineProvider, AppShell, Group, UnstyledButton } from '@mantine/core';
import { theme } from './theme';
import { Logs } from './features/logs';
import {
  QueryClient,
  QueryClientProvider,
} from '@tanstack/react-query'

export default function App() {
  const queryClient = new QueryClient()

  return (
    <MantineProvider theme={theme}>
      <QueryClientProvider client={queryClient}>
        <AppShell
          header={{height: 60}}
        >
          <AppShell.Header>
            <Group h="100%" px="md" justify="right">
              <Group ml="xl">
                <UnstyledButton>Logs</UnstyledButton>
              </Group>
            </Group>
          </AppShell.Header>
          <AppShell.Main>
            <Logs />
          </AppShell.Main>
        </AppShell>
      </QueryClientProvider>
    </MantineProvider>
  );
}
