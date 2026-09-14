import { cn } from 'cn'

import type { SlotResponse, UserResponse } from '../../api/types'
import EmptyState from '../../components/EmptyState'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../../components/ui/table'
import { claveDeInstante, hoyEnClinica, partesDelDia } from '../../services/clinicTime'
import RemoveShiftButton from './RemoveShiftButton'
import ShiftChip from './ShiftChip'
import { agruparTurnos } from './shiftKinds'

interface RosterTableProps {
  readonly dias: readonly string[]
  readonly veterinarios: readonly UserResponse[]
  readonly turnos: readonly SlotResponse[]
  readonly isLoading: boolean
}

function celda(veterinarioId: number, dia: string): string {
  return `${String(veterinarioId)}|${dia}`
}

/**
 * El cuadro de la semana: una fila por veterinario y una columna por día.
 *
 * Es la vista con la que una clínica arma la rotación: de un vistazo se ve qué
 * día nadie está de guardia o quién atiende toda la semana sin descanso.
 */
export default function RosterTable({ dias, veterinarios, turnos, isLoading }: RosterTableProps) {
  if (!isLoading && veterinarios.length === 0) {
    return (
      <EmptyState
        title="Todavía no hay veterinarios"
        description="Dalos de alta en Personal para asignarles turnos."
      />
    )
  }
  const hoy = hoyEnClinica()
  const porCelda = agruparTurnos(turnos, (turno) =>
    celda(turno.veterinarian_id, claveDeInstante(turno.starts_at)),
  )

  return (
    <div className="overflow-x-auto rounded-lg border" aria-busy={isLoading}>
      <Table className="min-w-4xl table-fixed">
        <TableHeader>
          <TableRow>
            <TableHead className="w-40">Veterinario</TableHead>
            {dias.map((dia) => {
              const { semana, numero } = partesDelDia(dia)
              return (
                <TableHead key={dia} className={cn('capitalize', dia === hoy && 'text-primary')}>
                  {semana} {numero}
                </TableHead>
              )
            })}
          </TableRow>
        </TableHeader>
        <TableBody>
          {veterinarios.map((veterinario) => {
            const nombre = `${veterinario.first_name} ${veterinario.last_name}`
            return (
              <TableRow key={veterinario.id}>
                <TableCell className="align-top font-medium whitespace-normal">{nombre}</TableCell>
                {dias.map((dia) => (
                  <TableCell key={dia} className="align-top whitespace-normal">
                    <div className="flex flex-col gap-1.5">
                      {(porCelda.get(celda(veterinario.id, dia)) ?? []).map((turno) => (
                        <ShiftChip key={turno.id} turno={turno}>
                          <RemoveShiftButton turno={turno} nombre={nombre} />
                        </ShiftChip>
                      ))}
                    </div>
                  </TableCell>
                ))}
              </TableRow>
            )
          })}
        </TableBody>
      </Table>
    </div>
  )
}
