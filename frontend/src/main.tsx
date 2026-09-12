import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { RouterProvider } from 'react-router'

import router from './router'
import './index.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Los listados del sistema se consultan con filtros del servidor, así que
      // reintentar en bucle ante un 4xx solo retrasa el error visible.
      retry: 1,
      staleTime: 30_000,
      refetchOnWindowFocus: false,
    },
  },
})

const container = document.getElementById('root')

if (!container) {
  throw new Error('No se encontró el elemento #root en el documento.')
}

createRoot(container).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  </StrictMode>,
)
