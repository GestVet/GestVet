import { useQuery } from '@tanstack/react-query'
import { useEffect, useRef } from 'react'

import { fetchAppointments } from '../../api/appointments'
import type { AppointmentStatus } from '../../api/types'
import { useNotifications } from '../../store/notifications'
import { useCan } from '../../store/session'

// Respaldo: el aviso llega al instante por el canal en tiempo real, que
// invalida esta consulta. El sondeo solo cubre un corte de ese canal.
const POLL_INTERVAL_MS = 60_000
const ACTIVOS = new Set<AppointmentStatus>(['pending', 'confirmed'])

/**
 * HU11: avisa al veterinario -de guardia o de respaldo- de una emergencia nueva.
 */
export function useVeterinarianEmergencyAlerts(): void {
  const esVeterinario = useCan('appointments.attend')
  const push = useNotifications((state) => state.push)
  const anterior = useRef<Set<number> | null>(null)

  const emergencias = useQuery({
    queryKey: ['appointments', 'alerts', 'emergencias'],
    queryFn: () => fetchAppointments({ is_emergency: true }),
    enabled: esVeterinario,
    refetchInterval: esVeterinario ? POLL_INTERVAL_MS : false,
    // Una emergencia puede llegar con la pestaña en segundo plano, que es
    // justo cuando React Query pausa el sondeo por defecto.
    refetchIntervalInBackground: true,
    refetchOnWindowFocus: false,
  })

  useEffect(() => {
    if (!esVeterinario || !emergencias.data) {
      return
    }
    const activas = emergencias.data.items.filter((cita) => ACTIVOS.has(cita.status))
    const previa = anterior.current
    if (previa !== null && activas.some((cita) => !previa.has(cita.id))) {
      push({
        tone: previa.size > 0 ? 'warning' : 'info',
        message:
          previa.size > 0
            ? 'Se te asignó otra emergencia y ya tienes una en curso.'
            : 'Se te asignó una nueva emergencia.',
      })
    }
    anterior.current = new Set(activas.map((cita) => cita.id))
  }, [emergencias.data, esVeterinario, push])
}
