import ComplaintForm from './ComplaintForm'
import OpenHospitalizationForm from './OpenHospitalizationForm'
import ReviewForm from './ReviewForm'

interface AppointmentExtraPanelProps {
  readonly extra: 'review' | 'complaint' | 'hospitalization'
  readonly appointmentId: number
  readonly veterinarianId: number
}

/** Qué panel mostrar bajo una cita: reseñarla, reclamarla o internarla, nunca dos a la vez. */
export default function AppointmentExtraPanel({
  extra,
  appointmentId,
  veterinarianId,
}: AppointmentExtraPanelProps) {
  if (extra === 'review') {
    return <ReviewForm veterinarianId={veterinarianId} />
  }
  if (extra === 'hospitalization') {
    return <OpenHospitalizationForm appointmentId={appointmentId} />
  }
  return <ComplaintForm appointmentId={appointmentId} />
}
