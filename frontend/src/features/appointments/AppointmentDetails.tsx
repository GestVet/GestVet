import type { AppointmentResponse } from '../../api/types'
import AppointmentHeader from './AppointmentHeader'
import AppointmentTabs from './AppointmentTabs'
import RiskConsentLine from './RiskConsentLine'

interface AppointmentDetailsProps {
  readonly cita: AppointmentResponse
}

/**
 * El detalle de una cita: de quién es arriba, lo que se hace con ella debajo.
 * En una emergencia, entre medio, quién aceptó el riesgo.
 */
export default function AppointmentDetails({ cita }: AppointmentDetailsProps) {
  return (
    <div className="flex flex-col gap-4">
      <AppointmentHeader cita={cita} />
      {cita.risk_consent_id === null ? null : <RiskConsentLine consentId={cita.risk_consent_id} />}
      <AppointmentTabs cita={cita} />
    </div>
  )
}
