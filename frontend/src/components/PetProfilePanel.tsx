import CollapsibleSection from './CollapsibleSection'
import PetClinicalProfileForm from './PetClinicalProfileForm'
import PetOwnerProfileForm from './PetOwnerProfileForm'
import PetProfileSummary from './PetProfileSummary'
import { Separator } from './ui/separator'

interface PetProfileLike {
  readonly id: number
  readonly species: string
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
 * La ficha siempre se ve entera. Los formularios para editarla arrancan
 * cerrados: se consultan mucho más de lo que se editan, y abiertos estiraban
 * la pantalla. El dueño edita lo que conoce de memoria, peso y esterilización
 * incluidos; el veterinario los confirma o corrige con lo que mide en consulta.
 */
export default function PetProfilePanel({
  mascota,
  canEditOwnerFields,
  canEditClinicalFields,
}: PetProfilePanelProps) {
  return (
    <CollapsibleSection title="Ficha">
      <PetProfileSummary mascota={mascota} />
      {canEditOwnerFields ? (
        <>
          <Separator />
          <CollapsibleSection
            as="h4"
            title="Editar ficha"
            description="Especie, raza, nacimiento, sexo, color, microchip, temperamento, peso, altura, esterilización y alergias."
            defaultOpen={false}
          >
            <PetOwnerProfileForm
              petId={mascota.id}
              species={mascota.species}
              breed={mascota.breed}
              birthDate={mascota.birth_date}
              sex={mascota.sex}
              color={mascota.color}
              microchipNumber={mascota.microchip_number}
              temperament={mascota.temperament}
              weightKg={mascota.weight_kg}
              heightCm={mascota.height_cm}
              isSterilized={mascota.is_sterilized}
              allergies={mascota.allergies}
            />
          </CollapsibleSection>
        </>
      ) : null}
      {canEditClinicalFields ? (
        <>
          <Separator />
          <CollapsibleSection
            as="h4"
            title="Datos clínicos"
            description="Nacimiento, peso, altura, esterilización y alergias, confirmados o corregidos en consulta."
            defaultOpen={false}
          >
            <PetClinicalProfileForm
              petId={mascota.id}
              birthDate={mascota.birth_date}
              weightKg={mascota.weight_kg}
              heightCm={mascota.height_cm}
              isSterilized={mascota.is_sterilized}
              allergies={mascota.allergies}
            />
          </CollapsibleSection>
        </>
      ) : null}
    </CollapsibleSection>
  )
}
