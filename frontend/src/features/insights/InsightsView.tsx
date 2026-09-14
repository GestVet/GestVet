import PageHeader from '../../components/PageHeader'
import CareRemindersSection from './CareRemindersSection'
import NoShowRisksSection from './NoShowRisksSection'
import PaymentAnomaliesSection from './PaymentAnomaliesSection'
import VeterinarianAlertsSection from './VeterinarianAlertsSection'

export default function InsightsView() {
  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Indicadores"
        description="Señales calculadas sobre lo que la clínica ya registra: nada de esto se envía a un servicio externo."
      />

      <CareRemindersSection />
      <NoShowRisksSection />
      <PaymentAnomaliesSection />
      <VeterinarianAlertsSection />
    </div>
  )
}
