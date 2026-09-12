import { useQuery } from '@tanstack/react-query'

import { clinicalEntriesQueryKey, fetchClinicalEntries } from '../../api/medicalRecords'
import ClinicalEntryList from '../../components/ClinicalEntryList'

interface PetHistoryProps {
  readonly petId: number
}

export default function PetHistory({ petId }: PetHistoryProps) {
  const historia = useQuery({
    queryKey: clinicalEntriesQueryKey(petId),
    queryFn: () => fetchClinicalEntries(petId),
  })

  return (
    <ClinicalEntryList
      items={historia.data?.items ?? []}
      isLoading={historia.isPending}
      petId={petId}
      canManageAttachments={false}
    />
  )
}
