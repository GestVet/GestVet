import { cn } from 'cn'

import { formatearDia, partesDelDia } from '../../services/clinicTime'

export interface DiaDeReserva {
  /** AAAA-MM-DD en la fecha de la clinica. */
  readonly key: string
  readonly disponible: boolean
  /** Horas de inicio disponibles ese día, sumando todos los veterinarios. */
  readonly disponibles: number
}

interface DayStripProps {
  readonly dias: readonly DiaDeReserva[]
  readonly seleccionado: string | null
  readonly onSelect: (key: string) => void
}

/**
 * Los proximos dias, en una tira que se desliza en el celular.
 *
 * Un dia sin horas libres se ve pero no se puede elegir: saber que el martes
 * no hay turnos tambien es informacion, y ocultarlo haria saltar la tira.
 */
export default function DayStrip({ dias, seleccionado, onSelect }: DayStripProps) {
  return (
    <div role="group" aria-label="Día" className="-mx-1 flex gap-2 overflow-x-auto px-1 pt-1 pb-2">
      {dias.map((dia) => {
        const { semana, numero, mes } = partesDelDia(dia.key)
        const elegido = dia.key === seleccionado
        const detalle = dia.disponible
          ? `${String(dia.disponibles)} horarios disponibles`
          : 'sin horarios disponibles'
        return (
          <button
            key={dia.key}
            type="button"
            aria-pressed={elegido}
            aria-label={`${formatearDia(dia.key)}, ${detalle}`}
            disabled={!dia.disponible}
            onClick={() => {
              onSelect(dia.key)
            }}
            className={cn(
              'flex min-w-15 shrink-0 flex-col items-center gap-0.5 rounded-lg border px-2 py-2 text-xs outline-none transition-colors focus-visible:ring-3 focus-visible:ring-ring/50 disabled:cursor-not-allowed disabled:opacity-40',
              elegido
                ? 'border-primary bg-primary text-primary-foreground'
                : 'border-input bg-card text-foreground enabled:hover:bg-muted',
            )}
          >
            <span>{semana}</span>
            <span className="text-lg leading-none font-semibold tabular-nums">{numero}</span>
            <span>{mes}</span>
            <span className="mt-0.5 whitespace-nowrap">
              {dia.disponible ? `${String(dia.disponibles)} horarios` : 'Sin horarios'}
            </span>
          </button>
        )
      })}
    </div>
  )
}
