import { useQuery } from '@tanstack/react-query'

import { clinicalEntriesQueryKey, fetchClinicalEntries } from '../../api/medicalRecords'
import ClinicalEntryList from '../../components/ClinicalEntryList'
import { useIsVeterinarian } from '../../store/session'
import ClinicalEntryForm from './ClinicalEntryForm'

interface ClientPetHistoryProps {
  readonly petId: number
}

export default function ClientPetHistory({ petId }: ClientPetHistoryProps) {
  const puedeCargar = useIsVeterinarian()
  const historia = useQuery({
    queryKey: clinicalEntriesQueryKey(petId),
    queryFn: () => fetchClinicalEntries(petId),
  })

  return (
    <div className="stack">
      <ClinicalEntryList items={historia.data?.items ?? []} isLoading={historia.isPending} />
      {puedeCargar ? <ClinicalEntryForm petId={petId} /> : null}
    </div>
  )
}
