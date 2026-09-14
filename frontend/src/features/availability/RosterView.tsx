import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { useState } from 'react'

import { fetchRoster, rosterQueryKey } from '../../api/availability'
import { fetchStaff, staffQueryKey } from '../../api/directory'
import PageHeader from '../../components/PageHeader'
import SectionCard from '../../components/SectionCard'
import {
  diasDeLaSemana,
  hoyEnClinica,
  lunesDe,
  ventanaDeSemana,
} from '../../services/clinicTime'
import RosterTable from './RosterTable'
import ShiftForm from './ShiftForm'
import TeamChangeRequests from './TeamChangeRequests'
import WeekNavigator from './WeekNavigator'
import WeeklyPlanForm from './WeeklyPlanForm'

/**
 * Turnos y guardias del equipo.
 *
 * La clínica decide quién atiende y quién cubre las emergencias cada día, como
 * en las veterinarias de Trujillo con atención de día y guardia de noche.
 */
export default function RosterView() {
  const [lunes, setLunes] = useState(() => lunesDe(hoyEnClinica()))
  const ventana = ventanaDeSemana(lunes)

  const personal = useQuery({ queryKey: staffQueryKey, queryFn: fetchStaff })
  const turnos = useQuery({
    queryKey: rosterQueryKey(lunes),
    queryFn: () => fetchRoster(ventana.desde, ventana.hasta),
    placeholderData: keepPreviousData,
  })
  const equipo = personal.data?.items ?? []
  const activos = equipo.filter((cuenta) => cuenta.is_active)

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Turnos y guardias"
        description="Quién atiende y quién cubre las emergencias cada día de la semana."
      />

      <SectionCard title="Semana" actions={<WeekNavigator lunes={lunes} onChange={setLunes} />}>
        <RosterTable
          dias={diasDeLaSemana(lunes)}
          veterinarios={activos}
          turnos={turnos.data?.items ?? []}
          isLoading={turnos.isPending || personal.isPending}
        />
      </SectionCard>

      <div className="grid items-start gap-6 xl:grid-cols-2">
        <WeeklyPlanForm veterinarios={activos} />
        <ShiftForm veterinarios={activos} />
      </div>

      <TeamChangeRequests veterinarios={equipo} />
    </div>
  )
}
