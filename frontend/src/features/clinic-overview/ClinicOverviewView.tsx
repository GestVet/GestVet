import PageHeader from '../../components/PageHeader'
import { useCan } from '../../store/session'
import PetsOverviewSections from './PetsOverviewSections'
import ServiceConsumptionSection from './ServiceConsumptionSection'

export default function ClinicOverviewView() {
  const vePets = useCan('pets.overview_read')
  const veServicios = useCan('payments.report')

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Panorama de la clínica"
        description="Mascotas registradas y servicios más consumidos, con datos que se actualizan al filtrar."
      />

      {vePets ? <PetsOverviewSections /> : null}
      {veServicios ? <ServiceConsumptionSection /> : null}
    </div>
  )
}
