import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'

import { fetchVaccinationCard, vaccinationCardQueryKey } from '../../api/medicalRecords'
import FormDialog from '../../components/FormDialog'
import Icon from '../../components/Icon'
import VaccinationCard from '../../components/VaccinationCard'
import VaccinationCardPdfButton from '../../components/VaccinationCardPdfButton'
import { Button } from '../../components/ui/button'
import { useCan } from '../../store/session'
import VaccinationForm from './VaccinationForm'

interface ClientPetVaccinationsProps {
  readonly petId: number
}

/** El carnet de vacunas visto por el personal; el veterinario además registra. */
export default function ClientPetVaccinations({ petId }: ClientPetVaccinationsProps) {
  const puedeRegistrar = useCan('clinical_records.write')
  const [registrando, setRegistrando] = useState(false)
  const carnet = useQuery({
    queryKey: vaccinationCardQueryKey(petId),
    queryFn: () => fetchVaccinationCard(petId),
  })

  return (
    <>
      <VaccinationCard
        summary={carnet.data?.summary ?? []}
        items={carnet.data?.items ?? []}
        isLoading={carnet.isPending}
        actions={
          <div className="flex flex-wrap items-start gap-2">
            <VaccinationCardPdfButton petId={petId} />
            {puedeRegistrar ? (
            <Button
              type="button"
              size="sm"
              onClick={() => {
                setRegistrando(true)
              }}
            >
              <Icon name="vacuna" size={14} />
              <span>Registrar vacuna</span>
            </Button>
            ) : null}
          </div>
        }
      />
      {puedeRegistrar ? (
        <FormDialog
          open={registrando}
          onOpenChange={setRegistrando}
          title="Registrar una vacuna"
          description="La próxima dosis se sugiere según la vacuna y la edad de la mascota. Puedes cambiarla."
          size="lg"
        >
          <VaccinationForm
            petId={petId}
            onDone={() => {
              setRegistrando(false)
            }}
          />
        </FormDialog>
      ) : null}
    </>
  )
}
