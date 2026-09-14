import type { FieldErrors, UseFormRegister } from 'react-hook-form'

import { MAX_NOMBRE_DE_MASCOTA } from '../../components/formRules'
import SectionHeading from '../../components/SectionHeading'
import SpeciesBreedFields from '../../components/SpeciesBreedFields'
import TextareaField from '../../components/TextareaField'
import TextField from '../../components/TextField'
import {
  LARGO_DNI,
  MAX_APELLIDO,
  MAX_NOMBRE,
  soloDigitos,
  soloLetras,
  soloTelefono,
} from '../../services/fieldRules'
import type { WalkInEmergencyFormValues } from './formValues'

interface WalkInEmergencyFieldsProps {
  readonly register: UseFormRegister<WalkInEmergencyFormValues>
  readonly errors: FieldErrors<WalkInEmergencyFormValues>
  readonly species: string
}

/** Los campos del alta exprés, separados del envío para no pasar de tamaño. */
export default function WalkInEmergencyFields({
  register,
  errors,
  species,
}: WalkInEmergencyFieldsProps) {
  return (
    <>
      <fieldset className="m-0 flex flex-col gap-4 border-0 p-0">
        <legend className="mb-3 p-0">
          <SectionHeading as="h2">Cliente</SectionHeading>
        </legend>
        <div className="grid gap-5 sm:grid-cols-2">
          <TextField
            id="first_name"
            label="Nombre"
            maxLength={MAX_NOMBRE}
            sanitize={soloLetras}
            field={register('first_name')}
            error={errors.first_name?.message}
          />
          <TextField
            id="last_name"
            label="Apellido"
            maxLength={MAX_APELLIDO}
            sanitize={soloLetras}
            field={register('last_name')}
            error={errors.last_name?.message}
          />
          <TextField
            id="document_id"
            label="DNI"
            inputMode="numeric"
            maxLength={LARGO_DNI}
            sanitize={soloDigitos}
            field={register('document_id')}
            error={errors.document_id?.message}
          />
          <TextField
            id="phone"
            label="Teléfono (si lo tiene a mano)"
            type="tel"
            inputMode="tel"
            sanitize={soloTelefono}
            field={register('phone')}
            error={errors.phone?.message}
          />
        </div>
      </fieldset>

      <fieldset className="m-0 flex flex-col gap-4 border-0 p-0">
        <legend className="mb-3 p-0">
          <SectionHeading as="h2">Mascota y emergencia</SectionHeading>
        </legend>
        <div className="grid gap-5 sm:grid-cols-2">
          <TextField
            id="pet_name"
            label="Nombre de la mascota"
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
          rows={2}
          field={register('description')}
          error={errors.description?.message}
        />
      </fieldset>
    </>
  )
}
