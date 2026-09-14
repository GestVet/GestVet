import type { PetResponse } from '../../api/types'
import PetProfilePanel from '../../components/PetProfilePanel'
import PetHistory from './PetHistory'
import PetHospitalizations from './PetHospitalizations'
import PetVaccinations from './PetVaccinations'

interface PetDetailsProps {
  readonly mascota: PetResponse
}

/** Lo que se despliega bajo una mascota: su ficha, sus vacunas, su historia y sus internaciones. */
export default function PetDetails({ mascota }: PetDetailsProps) {
  return (
    <div className="flex flex-col gap-8">
      <PetProfilePanel mascota={mascota} canEditOwnerFields={true} canEditClinicalFields={false} />
      <PetVaccinations petId={mascota.id} />
      <PetHistory petId={mascota.id} />
      <PetHospitalizations petId={mascota.id} />
    </div>
  )
}
