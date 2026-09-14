import { useQuery } from '@tanstack/react-query'

import { clinicalEntriesQueryKey, fetchClinicalEntries } from '../../api/medicalRecords'
import ClinicalEntryList from '../../components/ClinicalEntryList'
import CollapsibleSection from '../../components/CollapsibleSection'
import { useCan } from '../../store/session'
import ClinicalEntryForm from './ClinicalEntryForm'
import ClinicalSummaryPanel from './ClinicalSummaryPanel'

interface ClientPetHistoryProps {
  readonly petId: number
}

export default function ClientPetHistory({ petId }: ClientPetHistoryProps) {
  const puedeCargar = useCan('clinical_records.write')
  const historia = useQuery({
    queryKey: clinicalEntriesQueryKey(petId),
    queryFn: () => fetchClinicalEntries(petId),
  })

  return (
    <div className="flex flex-col gap-4">
      {puedeCargar ? <ClinicalSummaryPanel petId={petId} /> : null}
      <ClinicalEntryList
        items={historia.data?.items ?? []}
        isLoading={historia.isPending}
        petId={petId}
        canManageAttachments={puedeCargar}
      />
      {puedeCargar ? (
        <CollapsibleSection
          title="Agregar a la historia clínica"
          description="Consulta, cirugía, control o carta de consentimiento."
          defaultOpen={false}
        >
          <ClinicalEntryForm petId={petId} />
        </CollapsibleSection>
      ) : null}
    </div>
  )
}
