import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { useState } from 'react'

import { fetchRoster, rosterQueryKey } from '../../api/availability'
import { fetchStaff, staffQueryKey } from '../../api/directory'
import Icon from '../../components/Icon'
import PageHeader from '../../components/PageHeader'
import SectionCard from '../../components/SectionCard'
import { Button } from '../../components/ui/button'
import {
  diasDeLaSemana,
  hoyEnClinica,
  lunesDe,
  ventanaDeSemana,
} from '../../services/clinicTime'
import RosterDialogs, { type DialogoDeTurnos } from './RosterDialogs'
import RosterWeek from './RosterWeek'
import TeamChangeRequests from './TeamChangeRequests'
import WeekNavigator from './WeekNavigator'

/**
 * Turnos y guardias del equipo.
 *
 * La clínica decide quién atiende y quién cubre las emergencias cada día, como
 * en las veterinarias de Trujillo con atención de día y guardia de noche. El
 * cuadro ocupa la pantalla; cargar turnos se hace en una ventana, desde los
 * botones de arriba o desde la celda del día.
 */
export default function RosterView() {
  const [lunes, setLunes] = useState(() => lunesDe(hoyEnClinica()))
  const [dialogo, setDialogo] = useState<DialogoDeTurnos>(null)
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
        actions={
          <>
            <Button
              type="button"
              variant="outline"
              size="lg"
              className="h-10 px-4"
              onClick={() => {
                setDialogo({ tipo: 'semanal' })
              }}
            >
              <Icon name="repetir" size={16} />
              <span>Horario semanal</span>
            </Button>
            <Button
              type="button"
              size="lg"
              className="h-10 px-4"
              onClick={() => {
                setDialogo({ tipo: 'turno' })
              }}
            >
              <Icon name="agregar" size={16} />
              <span>Asignar turno</span>
            </Button>
          </>
        }
      />

      <SectionCard title="Semana" actions={<WeekNavigator lunes={lunes} onChange={setLunes} />}>
        <RosterWeek
          dias={diasDeLaSemana(lunes)}
          veterinarios={activos}
          turnos={turnos.data?.items ?? []}
          isLoading={turnos.isPending || personal.isPending}
          onAsignar={(veterinarioId, dia) => {
            setDialogo({ tipo: 'turno', veterinarioId, dia })
          }}
        />
      </SectionCard>

      <TeamChangeRequests veterinarios={equipo} />

      <RosterDialogs
        dialogo={dialogo}
        veterinarios={activos}
        onClose={() => {
          setDialogo(null)
        }}
      />
    </div>
  )
}
