import type { FieldErrors, UseFormRegister } from 'react-hook-form'

import FieldError from '../../components/FieldError'
import TextField from '../../components/TextField'
import type { WalkInEmergencyFormValues } from './formValues'

interface WalkInEmergencyFieldsProps {
  readonly register: UseFormRegister<WalkInEmergencyFormValues>
  readonly errors: FieldErrors<WalkInEmergencyFormValues>
}

/** Los campos del alta exprés, separados del envío para no pasar de tamaño. */
export default function WalkInEmergencyFields({ register, errors }: WalkInEmergencyFieldsProps) {
  return (
    <>
      <TextField
        id="first_name"
        label="Nombre"
        field={register('first_name')}
        error={errors.first_name?.message}
      />
      <TextField
        id="last_name"
        label="Apellido"
        field={register('last_name')}
        error={errors.last_name?.message}
      />
      <TextField
        id="document_id"
        label="DNI"
        inputMode="numeric"
        field={register('document_id')}
        error={errors.document_id?.message}
      />
      <TextField
        id="phone"
        label="Teléfono (si lo tiene a mano)"
        inputMode="tel"
        field={register('phone')}
      />
      <TextField
        id="pet_name"
        label="Nombre de la mascota"
        field={register('pet_name')}
        error={errors.pet_name?.message}
      />
      <TextField
        id="pet_species"
        label="Especie"
        field={register('pet_species')}
        error={errors.pet_species?.message}
      />

      <div className="field">
        <label htmlFor="description">Motivo de la emergencia (opcional)</label>
        <textarea id="description" rows={2} {...register('description')} />
        <FieldError message={errors.description?.message} />
      </div>
    </>
  )
}
