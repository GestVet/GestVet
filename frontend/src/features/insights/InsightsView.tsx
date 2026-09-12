import CareRemindersSection from './CareRemindersSection'
import NoShowRisksSection from './NoShowRisksSection'
import PaymentAnomaliesSection from './PaymentAnomaliesSection'
import VeterinarianAlertsSection from './VeterinarianAlertsSection'

export default function InsightsView() {
  return (
    <div className="stack">
      <div className="page-header">
        <div>
          <h1>Indicadores</h1>
          <p className="muted">
            Señales calculadas sobre lo que la clínica ya registra: nada de esto se envía a un
            servicio externo.
          </p>
        </div>
      </div>

      <CareRemindersSection />
      <NoShowRisksSection />
      <PaymentAnomaliesSection />
      <VeterinarianAlertsSection />
    </div>
  )
}
