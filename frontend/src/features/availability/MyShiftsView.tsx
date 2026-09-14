import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { useState } from 'react'

import {
  fetchMyChangeRequests,
  fetchMySlots,
  myChangeRequestsQueryKey,
  mySlotsQueryKey,
} from '../../api/availability'
import FormDialog from '../../components/FormDialog'
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
import { useCan } from '../../store/session'
import ChangeRequestForm from './ChangeRequestForm'
import ChangeRequestList from './ChangeRequestList'
import WeekNavigator from './WeekNavigator'
import WeekSchedule from './WeekSchedule'

/**
 * Los turnos del veterinario.
 *
 * Los asigna la clínica; acá se ven por semana. Si uno no le sirve, el pedido
 * de cambio le llega a la administración y la respuesta vuelve a esta pantalla.
 */
export default function MyShiftsView() {
  const [lunes, setLunes] = useState(() => lunesDe(hoyEnClinica()))
  const puedePedir = useCan('schedule.request_change')
  const [pidiendo, setPidiendo] = useState(false)
  const ventana = ventanaDeSemana(lunes)

  const turnos = useQuery({
    queryKey: [...mySlotsQueryKey, lunes],
    queryFn: () => fetchMySlots(ventana.desde, ventana.hasta),
    // Cambiar de semana deja la anterior a la vista hasta que llega la nueva.
    placeholderData: keepPreviousData,
  })
  const pedidos = useQuery({
    queryKey: myChangeRequestsQueryKey,
    queryFn: fetchMyChangeRequests,
    enabled: puedePedir,
  })
  const deLaSemana = turnos.data?.items ?? []

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Mis turnos"
        description="Los asigna la clínica. En atención recibes citas; en guardia, las emergencias."
      />

      <SectionCard title="Semana" actions={<WeekNavigator lunes={lunes} onChange={setLunes} />}>
        <WeekSchedule dias={diasDeLaSemana(lunes)} turnos={deLaSemana} isLoading={turnos.isPending} />
      </SectionCard>

      {puedePedir ? (
        <SectionCard
          title="Pedidos de cambio"
          description="La administración los revisa y te responde acá. Si acepta uno, reasigna el turno."
          actions={
            <Button
              type="button"
              onClick={() => {
                setPidiendo(true)
              }}
            >
              <Icon name="correo" size={16} />
              <span>Pedir un cambio</span>
            </Button>
          }
        >
          <ChangeRequestList
            pedidos={pedidos.data?.items ?? []}
            isLoading={pedidos.isPending}
            emptyMessage="Todavía no pediste cambios."
          />
        </SectionCard>
      ) : null}

      <FormDialog
        open={pidiendo}
        onOpenChange={setPidiendo}
        title="Pedir un cambio de turno"
        description="Cuenta qué necesitas. La administración lo revisa y te responde en esta pantalla."
      >
        <ChangeRequestForm
          turnos={deLaSemana}
          onDone={() => {
            setPidiendo(false)
          }}
        />
      </FormDialog>
    </div>
  )
}
