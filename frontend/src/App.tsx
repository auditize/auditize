import { PrimeReactProvider } from 'primereact/api';
// import { twMerge } from 'tailwind-merge';
// import Tailwind from 'primereact/passthrough/tailwind';
import 'primeicons/primeicons.css';
import LogList from './components/LogList';
import 'primereact/resources/themes/soho-light/theme.css';

import {
  QueryClient,
  QueryClientProvider,
} from '@tanstack/react-query'

import './App.css'

function App() {
  const queryClient = new QueryClient()

  return (
    // <PrimeReactProvider value={{ unstyled: true, pt: Tailwind, ptOptions: { mergeSections: true, mergeProps: true, classNameMergeFunction: twMerge } }}>
      <PrimeReactProvider>
      <QueryClientProvider client={queryClient}>
        <LogList />
      </QueryClientProvider>
      </PrimeReactProvider>
  )
}

export default App
