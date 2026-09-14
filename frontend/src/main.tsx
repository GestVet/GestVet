import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
// El de `react-router/dom` es el que le pasa `flushSync` de react-dom al
// router. Sin el, la opcion `flushSync` de `navigate` se ignora en silencio.
import { RouterProvider } from 'react-router/dom'

import router from './router'
import { logger, logUncaughtErrors } from './services/logger'
import './index.css'

logUncaughtErrors()

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

// React escribe estos errores en la consola por su cuenta. Pasarlos por el
// logger los deja con el mismo formato y nivel que el resto, junto con la pila
// de componentes, que es lo que dice en que pantalla ocurrio.
createRoot(container, {
  onUncaughtError: (error, info) => {
    logger.error({ err: error, componentStack: info.componentStack }, 'react.uncaught_error')
  },
  onCaughtError: (error, info) => {
    logger.error({ err: error, componentStack: info.componentStack }, 'react.caught_error')
  },
  onRecoverableError: (error, info) => {
    logger.warn({ err: error, componentStack: info.componentStack }, 'react.recoverable_error')
  },
}).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  </StrictMode>,
)
