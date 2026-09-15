import type { UseFormReturn } from 'react-hook-form'

import type { PetOwnerProfileValues } from './petOwnerProfileSchema'
import PetOwnerClinicalFields from './PetOwnerClinicalFields'
import PetOwnerIdentityFields from './PetOwnerIdentityFields'
import TextareaField from './TextareaField'

interface PetOwnerProfileFieldsProps {
  readonly formulario: UseFormReturn<PetOwnerProfileValues>
  readonly petId: number
}

export default function PetOwnerProfileFields({ formulario, petId }: PetOwnerProfileFieldsProps) {
  const { register, formState } = formulario
  const errores = formState.errors
  const id = (campo: string) => `${campo}-${String(petId)}`

  return (
    <>
      <div className="grid gap-5 sm:grid-cols-2">
        <PetOwnerIdentityFields formulario={formulario} petId={petId} />
        <PetOwnerClinicalFields formulario={formulario} petId={petId} />
      </div>
      <TextareaField
        id={id('allergies')}
        label="Alergias / condiciones crónicas"
        placeholder="Alergia a la penicilina, dermatitis"
        icon="alergia"
        rows={2}
        field={register('allergies')}
        error={errores.allergies?.message}
      />
    </>
  )
}
