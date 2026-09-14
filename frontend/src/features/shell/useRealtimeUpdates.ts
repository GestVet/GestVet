import { type QueryClient, type QueryKey, useQueryClient } from '@tanstack/react-query'
import { useEffect } from 'react'

import { appointmentsQueryKey } from '../../api/appointments'
import { availabilityQueryKey } from '../../api/availability'
import { fetchCurrentUser } from '../../api/auth'
import { api } from '../../services/api'
import { EventStreamError, readEventStream } from '../../services/eventStream'
import { logger } from '../../services/logger'
import { useSession } from '../../store/session'

const RECONEXION_INICIAL_MS = 1000
const RECONEXION_MAXIMA_MS = 30_000
const NO_AUTORIZADO = 401
// Cambiaron los permisos de la cuenta: se vuelve a pedir el perfil.
const TEMA_PERMISOS = 'permissions'

const realtimeLogger = logger.child({ module: 'realtime' })

// Que consultas quedan desactualizadas con cada tema. Invalidar por prefijo
// alcanza a todas las variantes: los listados filtrados y los avisos.
const CONSULTAS_POR_TEMA: Readonly<Partial<Record<string, QueryKey>>> = {
  appointments: appointmentsQueryKey,
  schedule: availabilityQueryKey,
}

function invalidarTodo(queryClient: QueryClient): void {
  for (const queryKey of Object.values(CONSULTAS_POR_TEMA)) {
    if (queryKey !== undefined) {
      void queryClient.invalidateQueries({ queryKey })
    }
  }
}

function esperar(ms: number, signal: AbortSignal): Promise<void> {
  return new Promise((resolve) => {
    const temporizador = setTimeout(resolve, ms)
    signal.addEventListener(
      'abort',
      () => {
        clearTimeout(temporizador)
        resolve()
      },
      { once: true },
    )
  })
}

/**
 * Mantiene abierto el canal de avisos, reconectando con espera creciente.
 *
 * Al reconectar despues de un corte se invalidan los temas conocidos: mientras
 * no hubo conexion pudo cambiar algo, y el aviso de ese cambio ya no va a llegar.
 * Por lo mismo, cada conexion vuelve a pedir los permisos de la cuenta.
 */
async function mantenerConexion(
  token: string,
  queryClient: QueryClient,
  signal: AbortSignal,
  refrescarCuenta: () => void,
): Promise<void> {
  const estado = { espera: RECONEXION_INICIAL_MS, huboCorte: false }
  const alRecibir = (tipo: string) => {
    if (tipo === 'ready') {
      realtimeLogger.info({ reconnected: estado.huboCorte }, 'realtime.connected')
      refrescarCuenta()
      if (estado.huboCorte) {
        invalidarTodo(queryClient)
      }
      estado.espera = RECONEXION_INICIAL_MS
      return
    }
    if (tipo === TEMA_PERMISOS) {
      refrescarCuenta()
      return
    }
    const queryKey = CONSULTAS_POR_TEMA[tipo]
    if (queryKey !== undefined) {
      void queryClient.invalidateQueries({ queryKey })
    }
  }

  while (!signal.aborted) {
    try {
      await readEventStream({
        url: `${api.defaults.baseURL ?? ''}/events`,
        token,
        signal,
        onEvent: (evento) => {
          alRecibir(evento.type)
        },
      })
    } catch (error) {
      // Cerrar la sesion o desmontar la aplicacion aborta la lectura a
      // proposito: no es un corte y no hay que reconectar.
      if (error instanceof DOMException && error.name === 'AbortError') {
        return
      }
      if (error instanceof EventStreamError && error.status === NO_AUTORIZADO) {
        realtimeLogger.warn('realtime.unauthorized')
        return
      }
      realtimeLogger.warn({ err: error, retryInMs: estado.espera }, 'realtime.disconnected')
    }
    estado.huboCorte = true
    await esperar(estado.espera, signal)
    estado.espera = Math.min(estado.espera * 2, RECONEXION_MAXIMA_MS)
  }
}

/**
 * Actualiza las pantallas abiertas cuando el servidor avisa un cambio.
 *
 * El aviso no trae datos: marca como desactualizadas las consultas del tema y
 * React Query vuelve a pedir solo las que estan en pantalla. Asi el veterinario
 * ve la reserva nueva y el cliente la confirmacion sin recargar ni esperar al
 * sondeo.
 */
export function useRealtimeUpdates(): void {
  const token = useSession((state) => state.token)
  const updateUser = useSession((state) => state.updateUser)
  const queryClient = useQueryClient()

  useEffect(() => {
    if (token === null) {
      return
    }
    const control = new AbortController()
    // Con un permiso menos, el menu y las guardas de ruta se actualizan solos
    // al cambiar la sesion, sin cerrar sesion ni recargar.
    const refrescarCuenta = () => {
      fetchCurrentUser()
        .then(updateUser)
        .catch((error: unknown) => {
          realtimeLogger.warn({ err: error }, 'realtime.profile_refresh_failed')
        })
    }
    void mantenerConexion(token, queryClient, control.signal, refrescarCuenta)
    return () => {
      control.abort()
    }
  }, [token, queryClient, updateUser])
}
