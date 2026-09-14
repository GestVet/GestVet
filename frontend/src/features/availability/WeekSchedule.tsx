import { cn } from 'cn'

import type { SlotResponse } from '../../api/types'
import { claveDeInstante, hoyEnClinica, partesDelDia } from '../../services/clinicTime'
import ShiftChip from './ShiftChip'
import { agruparTurnos } from './shiftKinds'

interface WeekScheduleProps {
  readonly dias: readonly string[]
  readonly turnos: readonly SlotResponse[]
  readonly isLoading: boolean
}

/**
 * La semana de un veterinario, un día por columna.
 *
 * En el celular los días bajan uno debajo del otro. Un día sin turnos dice
 * "Libre": saber que el martes no trabaja también es información.
 */
export default function WeekSchedule({ dias, turnos, isLoading }: WeekScheduleProps) {
  const hoy = hoyEnClinica()
  const porDia = agruparTurnos(turnos, (turno) => claveDeInstante(turno.starts_at))

  return (
    <ol
      aria-busy={isLoading}
      className="m-0 grid list-none gap-3 p-0 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-7"
    >
      {dias.map((dia) => {
        const { semana, numero, mes } = partesDelDia(dia)
        const delDia = porDia.get(dia) ?? []
        return (
          <li
            key={dia}
            className={cn(
              'flex flex-col gap-2 rounded-lg border bg-card p-3',
              dia === hoy && 'border-primary',
            )}
          >
            <p className="m-0 text-sm font-semibold capitalize">
              {semana} {numero} <span className="font-normal text-muted-foreground">{mes}</span>
              {dia === hoy ? <span className="ml-1 text-xs font-medium text-primary">Hoy</span> : null}
            </p>
            {delDia.length === 0 ? (
              <p className="m-0 text-xs text-muted-foreground">{isLoading ? 'Cargando…' : 'Libre'}</p>
            ) : (
              delDia.map((turno) => <ShiftChip key={turno.id} turno={turno} />)
            )}
          </li>
        )
      })}
    </ol>
  )
}
