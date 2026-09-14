import type { AppointmentResponse } from '../../api/types'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs'
import { useCan } from '../../store/session'
import ComplaintForm from './ComplaintForm'
import OpenHospitalizationForm from './OpenHospitalizationForm'
import PaymentPanel from './PaymentPanel'
import ReviewForm from './ReviewForm'

interface AppointmentDetailsProps {
  readonly cita: AppointmentResponse
}

/**
 * El detalle de una cita, en pestañas.
 *
 * Antes eran cuatro botones sueltos en la fila, cada uno abriendo su propio
 * panel. Qué pestañas aparecen sale de los permisos y del estado, la misma
 * regla que aplica el servidor; reseñar o internar solo tiene sentido con la
 * cita ya atendida.
 */
export default function AppointmentDetails({ cita }: AppointmentDetailsProps) {
  const puedeResenar = useCan('reviews.submit')
  const puedeReclamar = useCan('complaints.file')
  const puedeInternar = useCan('hospitalizations.manage')
  const atendida = cita.status === 'completed'

  return (
    <Tabs defaultValue="pago" className="gap-4">
      <TabsList className="flex-wrap">
        <TabsTrigger value="pago">Pago</TabsTrigger>
        {puedeResenar && atendida ? <TabsTrigger value="resena">Reseña</TabsTrigger> : null}
        {puedeReclamar ? <TabsTrigger value="reclamo">Reclamo</TabsTrigger> : null}
        {puedeInternar && atendida ? <TabsTrigger value="internacion">Internación</TabsTrigger> : null}
      </TabsList>

      <TabsContent value="pago">
        <PaymentPanel appointmentId={cita.id} appointmentStatus={cita.status} />
      </TabsContent>
      <TabsContent value="resena">
        <ReviewForm appointmentId={cita.id} veterinarianId={cita.veterinarian_id} />
      </TabsContent>
      <TabsContent value="reclamo">
        <ComplaintForm appointmentId={cita.id} />
      </TabsContent>
      <TabsContent value="internacion">
        <OpenHospitalizationForm appointmentId={cita.id} />
      </TabsContent>
    </Tabs>
  )
}
