import type { FieldErrors, UseFormRegister } from 'react-hook-form'

import PasswordField from '../../components/PasswordField'
import TextField from '../../components/TextField'
import {
  LARGO_DNI,
  MAX_APELLIDO,
  MAX_NOMBRE,
  MAX_TELEFONO,
  soloDigitos,
  soloLetras,
  soloTelefono,
} from '../../services/fieldRules'
import type { ProfileForm } from './profileSchema'

interface ProfileFieldsProps {
  readonly register: UseFormRegister<ProfileForm>
  readonly errors: FieldErrors<ProfileForm>
}

export default function ProfileFields({ register, errors }: ProfileFieldsProps) {
  return (
    <>
      <div className="grid items-start gap-5 sm:grid-cols-2">
        <TextField
          id="first_name"
          label="Nombre"
          autoComplete="given-name"
          maxLength={MAX_NOMBRE}
          sanitize={soloLetras}
          field={register('first_name')}
          error={errors.first_name?.message}
        />
        <TextField
          id="last_name"
          label="Apellido"
          autoComplete="family-name"
          maxLength={MAX_APELLIDO}
          sanitize={soloLetras}
          field={register('last_name')}
          error={errors.last_name?.message}
        />
        <TextField
          id="phone"
          label="Teléfono"
          type="tel"
          inputMode="tel"
          autoComplete="tel"
          maxLength={MAX_TELEFONO}
          sanitize={soloTelefono}
          field={register('phone')}
          error={errors.phone?.message}
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
      </div>
      <PasswordField
        id="new_password"
        label="Nueva contraseña"
        autoComplete="new-password"
        hint="Déjala vacía para conservar la actual."
        field={register('new_password')}
        error={errors.new_password?.message}
      />
    </>
  )
}
