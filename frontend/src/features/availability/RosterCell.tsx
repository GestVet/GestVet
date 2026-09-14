import { cn } from 'cn'

import type { SlotResponse } from '../../api/types'
import Icon from '../../components/Icon'
import { Button } from '../../components/ui/button'
import { partesDelDia } from '../../services/clinicTime'
import RemoveShiftButton from './RemoveShiftButton'
import ShiftChip from './ShiftChip'

interface RosterCellProps {
  readonly turnos: readonly SlotResponse[]
  readonly nombre: string
  readonly dia: string
  /** Un día que ya pasó no admite turnos nuevos. */
  readonly puedeAsignar: boolean
  readonly onAsignar: () => void
}

/** Los turnos de un veterinario en un día, con el atajo para agregarle otro. */
export default function RosterCell({ turnos, nombre, dia, puedeAsignar, onAsignar }: RosterCellProps) {
  const { semana, numero } = partesDelDia(dia)

  return (
    <div className="flex flex-col gap-1.5">
      {turnos.map((turno) => (
        <ShiftChip key={turno.id} turno={turno}>
          <RemoveShiftButton turno={turno} nombre={nombre} />
        </ShiftChip>
      ))}
      {puedeAsignar ? (
        <Button
          type="button"
          variant="ghost"
          size="sm"
          // Con turnos cargados, el atajo aparece al pasar por la fila o al llegar
          // con el teclado: así el cuadro no se llena de botones repetidos.
          className={cn(
            'h-7 justify-start gap-1 px-1.5 text-xs text-muted-foreground hover:text-foreground',
            turnos.length > 0 && 'opacity-0 group-hover:opacity-100 focus-visible:opacity-100',
          )}
          aria-label={`Asignar turno a ${nombre} el ${semana} ${String(numero)}`}
          onClick={onAsignar}
        >
          <Icon name="agregar" size={12} />
          <span>Asignar</span>
        </Button>
      ) : null}
    </div>
  )
}
