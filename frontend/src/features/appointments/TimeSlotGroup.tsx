import { cn } from 'cn'

import type { GridSlotResponse, SlotStatus } from '../../api/types'
import { Button } from '../../components/ui/button'
import { formatearHora } from '../../services/clinicTime'

const MS_POR_MINUTO = 60_000

interface TimeSlotGroupProps {
  /** Veterinario al que pertenecen estas horas. */
  readonly ofertaId: number
  readonly veterinario: string
  /** Mañana, tarde o noche. */
  readonly franja: string
  readonly slots: readonly GridSlotResponse[]
  /** La elección actual del formulario. */
  readonly veterinarianId: number
  readonly scheduledAt: string
  readonly durationMinutes: number
  readonly onSelect: (veterinarianId: number, time: string) => void
}

interface Eleccion {
  readonly inicio: number
  readonly fin: number
}

function motivo(status: SlotStatus): string | null {
  switch (status) {
    case 'available':
      return null
    case 'taken':
      return 'ocupada'
    case 'too_short':
      return 'no alcanza para la duración de la cita'
    case 'past':
      return 'ya pasó'
    case 'emergency':
      return 'el veterinario atiende una emergencia'
  }
}

type Apariencia = 'elegida' | 'dentro-de-la-cita' | 'atenuada' | 'normal' | 'no-disponible'

function apariencia(slot: GridSlotResponse, eleccion: Eleccion | null, hayEleccion: boolean): Apariencia {
  if (slot.status !== 'available') {
    return 'no-disponible'
  }
  const inicio = new Date(slot.time).getTime()
  if (eleccion !== null && inicio === eleccion.inicio) {
    return 'elegida'
  }
  if (eleccion !== null && inicio > eleccion.inicio && inicio < eleccion.fin) {
    return 'dentro-de-la-cita'
  }
  return hayEleccion ? 'atenuada' : 'normal'
}

const CLASES: Record<Apariencia, string> = {
  elegida: '',
  'dentro-de-la-cita': 'border-primary/40 bg-primary/10 text-primary',
  atenuada: 'opacity-60 hover:opacity-100',
  normal: '',
  'no-disponible': 'line-through disabled:opacity-40',
}

/**
 * Cada hora de un veterinario en una parte del día.
 *
 * Las que no se pueden tomar se ven tachadas en vez de desaparecer, y al
 * elegir una se marca el tramo que ocupa la cita y se atenúan las demás.
 */
export default function TimeSlotGroup({
  ofertaId,
  veterinario,
  franja,
  slots,
  veterinarianId,
  scheduledAt,
  durationMinutes,
  onSelect,
}: TimeSlotGroupProps) {
  const hayEleccion = scheduledAt !== ''
  const inicioElegido = new Date(scheduledAt).getTime()
  const eleccion: Eleccion | null =
    hayEleccion && ofertaId === veterinarianId
      ? { inicio: inicioElegido, fin: inicioElegido + durationMinutes * MS_POR_MINUTO }
      : null

  return (
    <div className="flex flex-col gap-1.5">
      <p className="m-0 text-xs font-medium text-muted-foreground">{franja}</p>
      <div role="group" aria-label={`${franja}, horas con ${veterinario}`} className="flex flex-wrap gap-2">
        {slots.map((slot) => {
          const aspecto = apariencia(slot, eleccion, hayEleccion)
          const razon = motivo(slot.status)
          const hora = formatearHora(slot.time)
          return (
            <Button
              key={slot.time}
              type="button"
              size="sm"
              variant={aspecto === 'elegida' ? 'default' : 'outline'}
              disabled={razon !== null}
              aria-pressed={razon === null ? aspecto === 'elegida' : undefined}
              aria-label={razon === null ? hora : `${hora}, ${razon}`}
              className={cn('h-9 min-w-20 px-3 tabular-nums', CLASES[aspecto])}
              onClick={() => {
                onSelect(ofertaId, slot.time)
              }}
            >
              {hora}
            </Button>
          )
        })}
      </div>
    </div>
  )
}
