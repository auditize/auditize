import { PrimeReactProvider } from 'primereact/api';
import { twMerge } from 'tailwind-merge';
import Tailwind from 'primereact/passthrough/tailwind';
import LogList from './components/LogList';

import {
  QueryClient,
  QueryClientProvider,
} from '@tanstack/react-query'

import './App.css'

function App() {
  const queryClient = new QueryClient()

  return (
    <PrimeReactProvider value={{ unstyled: true, pt: Tailwind, ptOptions: { mergeSections: true, mergeProps: true, classNameMergeFunction: twMerge } }}>
      <QueryClientProvider client={queryClient}>
        <LogList />
      </QueryClientProvider>
    </PrimeReactProvider>
  )
}

export default App
