import '@mantine/core/styles.css';
import '@mantine/dates/styles.css';
import { MantineProvider } from '@mantine/core';
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
        <Logs />
      </QueryClientProvider>
    </MantineProvider>
  );
}
