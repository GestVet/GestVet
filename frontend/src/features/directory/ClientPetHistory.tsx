import { useQuery } from '@tanstack/react-query'

import { clinicalEntriesQueryKey, fetchClinicalEntries } from '../../api/medicalRecords'
import ClinicalEntryList from '../../components/ClinicalEntryList'
import SectionHeading from '../../components/SectionHeading'
import { Separator } from '../../components/ui/separator'
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
    <div className="flex flex-col gap-4">
      <ClinicalEntryList
        items={historia.data?.items ?? []}
        isLoading={historia.isPending}
        petId={petId}
        canManageAttachments={puedeCargar}
      />
      {puedeCargar ? (
        <>
          <Separator />
          <SectionHeading as="h3">Agregar a la historia clínica</SectionHeading>
          <ClinicalEntryForm petId={petId} />
        </>
      ) : null}
    </div>
  )
}
