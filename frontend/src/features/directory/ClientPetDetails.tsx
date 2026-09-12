import type { PetResponse } from '../../api/types'
import PetProfilePanel from '../../components/PetProfilePanel'
import { useIsVeterinarian } from '../../store/session'
import ClientPetHistory from './ClientPetHistory'
import ClientPetHospitalizations from './ClientPetHospitalizations'

interface ClientPetDetailsProps {
  readonly mascota: PetResponse
}

/** Ficha, historia e internaciones de una mascota, vistas por el personal. */
export default function ClientPetDetails({ mascota }: ClientPetDetailsProps) {
  const esVeterinario = useIsVeterinarian()

  return (
    <div className="flex flex-col gap-8">
      <PetProfilePanel
        mascota={mascota}
        canEditOwnerFields={false}
        canEditClinicalFields={esVeterinario}
      />
      <ClientPetHistory petId={mascota.id} />
      <ClientPetHospitalizations petId={mascota.id} />
    </div>
  )
}
