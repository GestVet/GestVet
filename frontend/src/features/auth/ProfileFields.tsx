import type { FieldErrors, UseFormRegister } from 'react-hook-form'

import TextField from '../../components/TextField'
import type { ProfileForm } from './profileSchema'

interface ProfileFieldsProps {
  readonly register: UseFormRegister<ProfileForm>
  readonly errors: FieldErrors<ProfileForm>
}

export default function ProfileFields({ register, errors }: ProfileFieldsProps) {
  return (
    <>
      <div className="grid gap-5 sm:grid-cols-2">
        <TextField
          id="first_name"
          label="Nombre"
          autoComplete="given-name"
          field={register('first_name')}
          error={errors.first_name?.message}
        />
        <TextField
          id="last_name"
          label="Apellido"
          autoComplete="family-name"
          field={register('last_name')}
          error={errors.last_name?.message}
        />
        <TextField
          id="phone"
          label="Teléfono"
          type="tel"
          inputMode="tel"
          autoComplete="tel"
          field={register('phone')}
          error={errors.phone?.message}
        />
        <TextField
          id="document_id"
          label="DNI"
          inputMode="numeric"
          maxLength={8}
          field={register('document_id')}
          error={errors.document_id?.message}
        />
      </div>
      <TextField
        id="new_password"
        label="Nueva contraseña"
        type="password"
        autoComplete="new-password"
        hint="Dejala vacía para conservar la actual."
        field={register('new_password')}
        error={errors.new_password?.message}
      />
    </>
  )
}
