import '@mantine/core/styles.css';
import '@mantine/dates/styles.css';
import { MantineProvider } from '@mantine/core';
import { theme } from './theme';
import { LogList } from './components/LogList';
import {
  QueryClient,
  QueryClientProvider,
} from '@tanstack/react-query'

export default function App() {
  const queryClient = new QueryClient()

  return (
    <MantineProvider theme={theme}>
      <QueryClientProvider client={queryClient}>
        <LogList />
      </QueryClientProvider>
    </MantineProvider>
  );
}
