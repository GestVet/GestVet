import type { ReactNode } from 'react'

import type { SlotResponse } from '../../api/types'
import StatusBadge from '../../components/StatusBadge'
import { ETIQUETA_DE_TURNO, horarioDeTurno, TONO_DE_TURNO } from './shiftKinds'

interface ShiftChipProps {
  readonly turno: SlotResponse
  /** Acciones del turno, a la derecha. */
  readonly children?: ReactNode
}

/** Un turno en una celda: si es atención o guardia, y de qué hora a qué hora. */
export default function ShiftChip({ turno, children }: ShiftChipProps) {
  return (
    <div className="flex items-start justify-between gap-1 rounded-md border bg-background px-2 py-1.5">
      <div className="flex min-w-0 flex-col items-start gap-1">
        <StatusBadge label={ETIQUETA_DE_TURNO[turno.kind]} tone={TONO_DE_TURNO[turno.kind]} />
        <span className="text-xs tabular-nums">{horarioDeTurno(turno)}</span>
      </div>
      {children}
    </div>
  )
}
