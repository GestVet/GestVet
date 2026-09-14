import { cn } from 'cn'

import type { SlotResponse, UserResponse } from '../../api/types'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../../components/ui/table'
import { claveDeInstante, hoyEnClinica, partesDelDia } from '../../services/clinicTime'
import RosterCell from './RosterCell'
import { agruparTurnos } from './shiftKinds'

interface RosterTableProps {
  readonly dias: readonly string[]
  readonly veterinarios: readonly UserResponse[]
  readonly turnos: readonly SlotResponse[]
  readonly isLoading: boolean
  readonly onAsignar: (veterinarioId: number, dia: string) => void
}

function celda(veterinarioId: number, dia: string): string {
  return `${String(veterinarioId)}|${dia}`
}

/**
 * El cuadro de la semana: una fila por veterinario y una columna por día.
 *
 * Es la vista con la que una clínica arma la rotación: de un vistazo se ve qué
 * día nadie está de guardia o quién atiende toda la semana sin descanso. Solo
 * se muestra desde pantallas anchas; en el celular la semana va por días.
 */
export default function RosterTable({
  dias,
  veterinarios,
  turnos,
  isLoading,
  onAsignar,
}: RosterTableProps) {
  const hoy = hoyEnClinica()
  const porCelda = agruparTurnos(turnos, (turno) =>
    celda(turno.veterinarian_id, claveDeInstante(turno.starts_at)),
  )

  return (
    <div className="hidden rounded-lg border lg:block" aria-busy={isLoading}>
      <Table className="min-w-4xl table-fixed" aria-label="Turnos de la semana por veterinario">
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
              <TableRow key={veterinario.id} className="group">
                <TableCell className="align-top font-medium whitespace-normal">{nombre}</TableCell>
                {dias.map((dia) => (
                  <TableCell key={dia} className="align-top whitespace-normal">
                    <RosterCell
                      turnos={porCelda.get(celda(veterinario.id, dia)) ?? []}
                      nombre={nombre}
                      dia={dia}
                      puedeAsignar={dia >= hoy}
                      onAsignar={() => {
                        onAsignar(veterinario.id, dia)
                      }}
                    />
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
