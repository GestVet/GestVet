import type { Control, FieldErrors, UseFormRegister } from 'react-hook-form'

import PhoneField from '../../components/PhoneField'
import SectionHeading from '../../components/SectionHeading'
import TextField from '../../components/TextField'
import {
  LARGO_DNI,
  MAX_APELLIDO,
  MAX_NOMBRE,
  soloDigitos,
  soloLetras,
} from '../../services/fieldRules'
import type { WalkInEmergencyFormValues } from './formValues'

interface WalkInClientFieldsProps {
  readonly register: UseFormRegister<WalkInEmergencyFormValues>
  readonly control: Control<WalkInEmergencyFormValues>
  readonly errors: FieldErrors<WalkInEmergencyFormValues>
}

/** Los datos del cliente que llega sin cuenta: lo justo para abrir la emergencia. */
export default function WalkInClientFields({ register, control, errors }: WalkInClientFieldsProps) {
  return (
    <fieldset className="m-0 flex flex-col gap-4 border-0 p-0">
      <legend className="mb-3 p-0">
        <SectionHeading as="h2">Cliente</SectionHeading>
      </legend>
      <div className="grid gap-5 sm:grid-cols-2">
        <TextField
          id="first_name"
          label="Nombre"
          placeholder="María"
          icon="perfil"
          maxLength={MAX_NOMBRE}
          sanitize={soloLetras}
          field={register('first_name')}
          error={errors.first_name?.message}
        />
        <TextField
          id="last_name"
          label="Apellido"
          placeholder="Quispe Rojas"
          icon="perfil"
          maxLength={MAX_APELLIDO}
          sanitize={soloLetras}
          field={register('last_name')}
          error={errors.last_name?.message}
        />
        <TextField
          id="document_id"
          label="DNI"
          placeholder="12345678"
          icon="documento"
          inputMode="numeric"
          maxLength={LARGO_DNI}
          sanitize={soloDigitos}
          field={register('document_id')}
          error={errors.document_id?.message}
        />
        <PhoneField
          id="phone"
          label="Teléfono (si lo tiene a mano)"
          control={control}
          name="phone"
          error={errors.phone?.message}
        />
      </div>
    </fieldset>
  )
}
