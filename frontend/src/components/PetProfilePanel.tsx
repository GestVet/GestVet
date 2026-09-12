import PetClinicalProfileForm from './PetClinicalProfileForm'
import PetOwnerProfileForm from './PetOwnerProfileForm'
import PetProfileSummary from './PetProfileSummary'

interface PetProfileLike {
  readonly id: number
  readonly breed: string
  readonly birth_date: string
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
 * memoria, raza incluida; el veterinario, lo que mide o confirma en consulta,
 * y también la fecha de nacimiento, que en una emergencia queda provisoria.
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
          breed={mascota.breed}
          sex={mascota.sex}
          color={mascota.color}
          microchipNumber={mascota.microchip_number}
          temperament={mascota.temperament}
        />
      ) : null}
      {canEditClinicalFields ? (
        <PetClinicalProfileForm
          petId={mascota.id}
          birthDate={mascota.birth_date}
          weightKg={mascota.weight_kg}
          heightCm={mascota.height_cm}
          isSterilized={mascota.is_sterilized}
          allergies={mascota.allergies}
        />
      ) : null}
    </div>
  )
}
