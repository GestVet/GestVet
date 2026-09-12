import PetClinicalProfileForm from './PetClinicalProfileForm'
import PetOwnerProfileForm from './PetOwnerProfileForm'
import PetProfileSummary from './PetProfileSummary'

interface PetProfileLike {
  readonly id: number
  readonly sex: 'male' | 'female' | null
  readonly color: string
  readonly microchip_number: string
  readonly temperament: string
  readonly weight_kg: string | null
  readonly height_cm: string | null
  readonly is_sterilized: boolean | null
  readonly allergies: string
}

interface PetProfilePanelProps {
  readonly mascota: PetProfileLike
  readonly canEditOwnerFields: boolean
  readonly canEditClinicalFields: boolean
}

/**
 * Ficha completa de la mascota, con la parte editable que corresponda.
 *
 * La ficha siempre se ve entera: lo que cambia según quién mira es si además
 * aparece un formulario para editarla. El dueño edita lo que conoce de
 * memoria; el veterinario, lo que mide o confirma en consulta.
 */
export default function PetProfilePanel({
  mascota,
  canEditOwnerFields,
  canEditClinicalFields,
}: PetProfilePanelProps) {
  return (
    <div className="stack">
      <PetProfileSummary mascota={mascota} />
      {canEditOwnerFields ? (
        <PetOwnerProfileForm
          petId={mascota.id}
          sex={mascota.sex}
          color={mascota.color}
          microchipNumber={mascota.microchip_number}
          temperament={mascota.temperament}
        />
      ) : null}
      {canEditClinicalFields ? (
        <PetClinicalProfileForm
          petId={mascota.id}
          weightKg={mascota.weight_kg}
          heightCm={mascota.height_cm}
          isSterilized={mascota.is_sterilized}
          allergies={mascota.allergies}
        />
      ) : null}
    </div>
  )
}
