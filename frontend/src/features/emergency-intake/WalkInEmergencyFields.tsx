import type { Control, FieldErrors, UseFormRegister } from 'react-hook-form'

import { MAX_NOMBRE_DE_MASCOTA } from '../../components/formRules'
import SectionHeading from '../../components/SectionHeading'
import SpeciesBreedFields from '../../components/SpeciesBreedFields'
import TextareaField from '../../components/TextareaField'
import TextField from '../../components/TextField'
import type { WalkInEmergencyFormValues } from './formValues'
import WalkInClientFields from './WalkInClientFields'

interface WalkInEmergencyFieldsProps {
  readonly register: UseFormRegister<WalkInEmergencyFormValues>
  readonly control: Control<WalkInEmergencyFormValues>
  readonly errors: FieldErrors<WalkInEmergencyFormValues>
  readonly species: string
}

/** Los campos del alta exprés, separados del envío para no pasar de tamaño. */
export default function WalkInEmergencyFields({
  register,
  control,
  errors,
  species,
}: WalkInEmergencyFieldsProps) {
  return (
    <>
      <WalkInClientFields register={register} control={control} errors={errors} />

      <fieldset className="m-0 flex flex-col gap-4 border-0 p-0">
        <legend className="mb-3 p-0">
          <SectionHeading as="h2">Mascota y emergencia</SectionHeading>
        </legend>
        <div className="grid gap-5 sm:grid-cols-2">
          <TextField
            id="pet_name"
            label="Nombre de la mascota"
            placeholder="Firulais"
            icon="mascota"
            maxLength={MAX_NOMBRE_DE_MASCOTA}
            field={register('pet_name')}
            error={errors.pet_name?.message}
          />
          <SpeciesBreedFields
            idPrefix="emergencia"
            species={species}
            speciesField={register('pet_species')}
            speciesError={errors.pet_species?.message}
          />
        </div>
        <TextareaField
          id="description"
          label="Motivo de la emergencia (opcional)"
          placeholder="Lo atropelló un auto y sangra de una pata"
          icon="emergencia"
          rows={2}
          field={register('description')}
          error={errors.description?.message}
        />
      </fieldset>
    </>
  )
}
