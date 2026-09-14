import { useQuery } from '@tanstack/react-query'
import { useEffect, useRef } from 'react'

import { fetchAppointments } from '../../api/appointments'
import type { AppointmentResponse, AppointmentStatus } from '../../api/types'
import { type Toast, useNotifications } from '../../store/notifications'
import { useSession } from '../../store/session'

// Respaldo: el cambio de estado llega al instante por el canal en tiempo real,
// que invalida esta consulta. El sondeo solo cubre un corte de ese canal.
const POLL_INTERVAL_MS = 60_000

const MENSAJE_POR_ESTADO: Partial<Record<AppointmentStatus, string>> = {
  confirmed: 'Tu cita fue confirmada.',
  completed: 'Tu cita fue completada.',
  cancelled: 'Tu cita fue cancelada.',
}

function avisoPara(cita: AppointmentResponse): string | null {
  const mensaje = MENSAJE_POR_ESTADO[cita.status]
  if (mensaje === undefined) {
    return null
  }
  if (cita.status === 'cancelled' && cita.cancellation_reason) {
    return `${mensaje} Motivo: ${cita.cancellation_reason}`
  }
  return mensaje
}

function notificarSiCambio(
  cita: AppointmentResponse,
  previa: Map<number, AppointmentStatus>,
  push: (toast: Omit<Toast, 'id'>) => void,
): void {
  const antes = previa.get(cita.id)
  if (antes === undefined || antes === cita.status) {
    return
  }
  const aviso = avisoPara(cita)
  if (aviso === null) {
    return
  }
  push({ tone: cita.status === 'cancelled' ? 'warning' : 'info', message: aviso })
}

/**
 * HU12: avisa al cliente cuando el veterinario cambia el estado de su cita.
 *
 * El original lo hacía con `sessionStorage` y un `alert()` por página; acá
 * vive en el armazón de la aplicación y compara contra la última foto vista.
 */
export function useClientAppointmentAlerts(): void {
  const esCliente = useSession((state) => state.user?.role === 'client')
  const push = useNotifications((state) => state.push)
  const anterior = useRef<Map<number, AppointmentStatus> | null>(null)

  const citas = useQuery({
    queryKey: ['appointments', 'alerts', 'cliente'],
    queryFn: () => fetchAppointments(),
    enabled: esCliente,
    refetchInterval: esCliente ? POLL_INTERVAL_MS : false,
    // El aviso importa más justo cuando la pestaña no tiene el foco: por
    // defecto React Query pausa el sondeo ahí, que es lo opuesto de lo que
    // este caso necesita.
    refetchIntervalInBackground: true,
    refetchOnWindowFocus: false,
  })

  useEffect(() => {
    if (!esCliente || !citas.data) {
      return
    }
    const previa = anterior.current
    if (previa !== null) {
      for (const cita of citas.data.items) {
        notificarSiCambio(cita, previa, push)
      }
    }
    anterior.current = new Map(citas.data.items.map((cita) => [cita.id, cita.status]))
  }, [citas.data, esCliente, push])
}
