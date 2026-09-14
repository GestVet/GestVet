import { useQuery } from '@tanstack/react-query'

import { fetchVaccinationCard, vaccinationCardQueryKey } from '../../api/medicalRecords'
import VaccinationCard from '../../components/VaccinationCard'
import VaccinationCardPdfButton from '../../components/VaccinationCardPdfButton'

interface PetVaccinationsProps {
  readonly petId: number
}

/** El carnet de vacunas que ve el dueño: solo lectura, lo registra el veterinario. */
export default function PetVaccinations({ petId }: PetVaccinationsProps) {
  const carnet = useQuery({
    queryKey: vaccinationCardQueryKey(petId),
    queryFn: () => fetchVaccinationCard(petId),
  })

  return (
    <VaccinationCard
      summary={carnet.data?.summary ?? []}
      items={carnet.data?.items ?? []}
      isLoading={carnet.isPending}
      actions={<VaccinationCardPdfButton petId={petId} />}
    />
  )
}
