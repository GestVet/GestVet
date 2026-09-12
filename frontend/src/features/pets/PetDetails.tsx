import type { PetResponse } from '../../api/types'
import PetProfilePanel from '../../components/PetProfilePanel'
import PetHistory from './PetHistory'
import PetHospitalizations from './PetHospitalizations'

interface PetDetailsProps {
  readonly mascota: PetResponse
}

/** Lo que se despliega bajo una mascota: su ficha, su historia y sus internaciones. */
export default function PetDetails({ mascota }: PetDetailsProps) {
  return (
    <div className="flex flex-col gap-8">
      <PetProfilePanel mascota={mascota} canEditOwnerFields={true} canEditClinicalFields={false} />
      <PetHistory petId={mascota.id} />
      <PetHospitalizations petId={mascota.id} />
    </div>
  )
}
