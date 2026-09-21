import type { AppointmentResponse } from '../../api/types'
import AppointmentHeader from './AppointmentHeader'
import AppointmentTabs from './AppointmentTabs'

interface AppointmentDetailsProps {
  readonly cita: AppointmentResponse
}

/** El detalle de una cita: de quién es arriba, lo que se hace con ella debajo. */
export default function AppointmentDetails({ cita }: AppointmentDetailsProps) {
  return (
    <div className="flex flex-col gap-4">
      <AppointmentHeader cita={cita} />
      <AppointmentTabs cita={cita} />
    </div>
  )
}
