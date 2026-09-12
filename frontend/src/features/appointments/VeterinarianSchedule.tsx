import { useQuery } from '@tanstack/react-query'
import type { ReactNode } from 'react'

import { fetchSlotsOfVeterinarian, slotsOfVeterinarianQueryKey } from '../../api/availability'

const FORMATO = new Intl.DateTimeFormat('es-PE', { dateStyle: 'medium', timeStyle: 'short' })

interface VeterinarianScheduleProps {
  readonly veterinarianId: number
}

/**
 * Tramos publicados por el veterinario elegido en la reserva.
 *
 * HU06 pedía verlos antes de reservar, no solo un texto de ayuda genérico.
 */
export default function VeterinarianSchedule({ veterinarianId }: VeterinarianScheduleProps) {
  const horario = useQuery({
    queryKey: slotsOfVeterinarianQueryKey(veterinarianId),
    queryFn: () => fetchSlotsOfVeterinarian(veterinarianId),
    enabled: veterinarianId > 0,
  })

  if (veterinarianId <= 0) {
    return null
  }

  const items = horario.data?.items ?? []
  let contenido: ReactNode
  if (horario.isPending) {
    contenido = <p className="empty">Cargando…</p>
  } else if (items.length === 0) {
    contenido = <p className="empty">Todavía no publicó ningún tramo.</p>
  } else {
    contenido = (
      <ul>
        {items.map((tramo) => (
          <li key={tramo.id}>
            {FORMATO.format(new Date(tramo.starts_at))} –{' '}
            {FORMATO.format(new Date(tramo.ends_at))}
          </li>
        ))}
      </ul>
    )
  }

  return (
    <div className="field">
      <span className="muted">Horario publicado por este veterinario</span>
      {contenido}
    </div>
  )
}
