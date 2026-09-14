import type { SlotResponse, UserResponse } from '../../api/types'
import EmptyState from '../../components/EmptyState'
import { claveDeInstante, hoyEnClinica } from '../../services/clinicTime'
import RosterDayCard from './RosterDayCard'
import RosterTable from './RosterTable'
import { agruparTurnos } from './shiftKinds'

interface RosterWeekProps {
  readonly dias: readonly string[]
  readonly veterinarios: readonly UserResponse[]
  readonly turnos: readonly SlotResponse[]
  readonly isLoading: boolean
  /** Sin veterinario, se elige en la ventana: en el celular se asigna por día. */
  readonly onAsignar: (veterinarioId: number | undefined, dia: string) => void
}

/**
 * La semana del equipo, con la forma que mejor se lee en cada pantalla.
 *
 * En pantallas anchas, el cuadro de veterinarios por días. En el celular, un
 * cuadro de ocho columnas obliga a desplazarse de costado y aprieta cada
 * turno, así que los días bajan uno debajo del otro con quién trabaja en cada
 * uno.
 */
export default function RosterWeek({
  dias,
  veterinarios,
  turnos,
  isLoading,
  onAsignar,
}: RosterWeekProps) {
  if (!isLoading && veterinarios.length === 0) {
    return (
      <EmptyState
        title="Todavía no hay veterinarios"
        description="Dalos de alta en Personal para asignarles turnos."
      />
    )
  }
  const hoy = hoyEnClinica()
  const porDia = agruparTurnos(turnos, (turno) => claveDeInstante(turno.starts_at))
  const nombres = new Map(
    veterinarios.map((veterinario) => [
      veterinario.id,
      `${veterinario.first_name} ${veterinario.last_name}`,
    ]),
  )
  const vacio = isLoading ? 'Cargando…' : 'Nadie asignado'

  return (
    <>
      <RosterTable
        dias={dias}
        veterinarios={veterinarios}
        turnos={turnos}
        isLoading={isLoading}
        onAsignar={onAsignar}
      />
      <ol aria-busy={isLoading} className="m-0 flex list-none flex-col gap-3 p-0 lg:hidden">
        {dias.map((dia) => (
          <RosterDayCard
            key={dia}
            dia={dia}
            esHoy={dia === hoy}
            puedeAsignar={dia >= hoy}
            turnos={porDia.get(dia) ?? []}
            vacio={vacio}
            nombreDe={(id) => nombres.get(id) ?? `Veterinario #${String(id)}`}
            onAsignar={() => {
              onAsignar(undefined, dia)
            }}
          />
        ))}
      </ol>
    </>
  )
}
