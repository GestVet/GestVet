import { useState } from 'react'

import type { AppointmentResponse } from '../../api/types'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs'
import { useCan } from '../../store/session'
import ComplaintForm from './ComplaintForm'
import ConsentsPanel from './ConsentsPanel'
import OpenHospitalizationForm from './OpenHospitalizationForm'
import PaymentPanel from './PaymentPanel'
import type { RequestableKind } from './requestConsentSchema'
import ReviewForm from './ReviewForm'

interface AppointmentTabsProps {
  readonly cita: AppointmentResponse
}

/**
 * Lo que se hace con una cita, en pestañas.
 *
 * Antes eran cuatro botones sueltos en la fila, cada uno abriendo su propio
 * panel. Qué pestañas aparecen sale de los permisos y del estado, la misma
 * regla que aplica el servidor; reseñar o internar solo tiene sentido con la
 * cita ya atendida. Las pestañas son controladas para que la internación
 * rechazada por falta de consentimiento lleve directo a pedirlo.
 */
export default function AppointmentTabs({ cita }: AppointmentTabsProps) {
  const puedeResenar = useCan('reviews.submit')
  const puedeReclamar = useCan('complaints.file')
  const puedeInternar = useCan('hospitalizations.manage')
  const pideConsentimientos = useCan('consents.request')
  const respondeConsentimientos = useCan('consents.respond')
  const veConsentimientos = pideConsentimientos || respondeConsentimientos
  const atendida = cita.status === 'completed'
  const [pestana, setPestana] = useState('pago')
  const [atajo, setAtajo] = useState<RequestableKind | undefined>(undefined)

  return (
    <Tabs
      value={pestana}
      onValueChange={(valor) => {
        setPestana(valor)
        // El atajo abre el pedido una sola vez; volver a la pestaña no lo repite.
        setAtajo(undefined)
      }}
      className="gap-4"
    >
      <TabsList className="flex-wrap">
        <TabsTrigger value="pago">Pago</TabsTrigger>
        {veConsentimientos ? (
          <TabsTrigger value="consentimientos">Consentimientos</TabsTrigger>
        ) : null}
        {puedeResenar && atendida ? <TabsTrigger value="resena">Reseña</TabsTrigger> : null}
        {puedeReclamar ? <TabsTrigger value="reclamo">Reclamo</TabsTrigger> : null}
        {puedeInternar && atendida ? <TabsTrigger value="internacion">Internación</TabsTrigger> : null}
      </TabsList>

      <TabsContent value="pago">
        <PaymentPanel appointmentId={cita.id} appointmentStatus={cita.status} />
      </TabsContent>
      <TabsContent value="consentimientos">
        <ConsentsPanel appointmentId={cita.id} initialRequest={atajo} />
      </TabsContent>
      <TabsContent value="resena">
        <ReviewForm appointmentId={cita.id} veterinarianId={cita.veterinarian_id} />
      </TabsContent>
      <TabsContent value="reclamo">
        <ComplaintForm appointmentId={cita.id} />
      </TabsContent>
      <TabsContent value="internacion">
        <OpenHospitalizationForm
          appointmentId={cita.id}
          onRequestConsent={() => {
            setAtajo('hospitalization')
            setPestana('consentimientos')
          }}
        />
      </TabsContent>
    </Tabs>
  )
}
