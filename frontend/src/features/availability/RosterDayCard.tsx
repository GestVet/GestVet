import { cn } from 'cn'

import type { SlotResponse } from '../../api/types'
import Icon from '../../components/Icon'
import { Button } from '../../components/ui/button'
import { partesDelDia } from '../../services/clinicTime'
import RemoveShiftButton from './RemoveShiftButton'
import ShiftChip from './ShiftChip'

interface RosterDayCardProps {
  readonly dia: string
  readonly esHoy: boolean
  readonly puedeAsignar: boolean
  readonly turnos: readonly SlotResponse[]
  readonly vacio: string
  readonly nombreDe: (veterinarioId: number) => string
  readonly onAsignar: () => void
}

/** Un día de la semana en el celular: quién trabaja y el botón para asignar a alguien más. */
export default function RosterDayCard({
  dia,
  esHoy,
  puedeAsignar,
  turnos,
  vacio,
  nombreDe,
  onAsignar,
}: RosterDayCardProps) {
  const { semana, numero, mes } = partesDelDia(dia)

  return (
    <li className={cn('flex flex-col gap-3 rounded-lg border bg-card p-3', esHoy && 'border-primary')}>
      <div className="flex items-center justify-between gap-2">
        <h3 className="m-0 text-sm font-semibold capitalize">
          {semana} {numero} <span className="font-normal text-muted-foreground">{mes}</span>
          {esHoy ? <span className="ml-1 text-xs font-medium text-primary normal-case">Hoy</span> : null}
        </h3>
        {puedeAsignar ? (
          <Button
            type="button"
            size="sm"
            variant="outline"
            aria-label={`Asignar un turno el ${semana} ${String(numero)}`}
            onClick={onAsignar}
          >
            <Icon name="agregar" size={14} />
            <span>Asignar</span>
          </Button>
        ) : null}
      </div>
      {turnos.length === 0 ? (
        <p className="m-0 text-xs text-muted-foreground">{vacio}</p>
      ) : (
        <ul className="m-0 flex list-none flex-col gap-2 p-0">
          {turnos.map((turno) => {
            const nombre = nombreDe(turno.veterinarian_id)
            return (
              <li key={turno.id} className="flex flex-col gap-1">
                <span className="text-xs font-medium">{nombre}</span>
                <ShiftChip turno={turno}>
                  <RemoveShiftButton turno={turno} nombre={nombre} />
                </ShiftChip>
              </li>
            )
          })}
        </ul>
      )}
    </li>
  )
}
