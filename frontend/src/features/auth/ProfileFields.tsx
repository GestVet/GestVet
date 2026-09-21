import type { Control, FieldErrors, UseFormRegister } from 'react-hook-form'

import PasswordField from '../../components/PasswordField'
import PhoneField from '../../components/PhoneField'
import TextField from '../../components/TextField'
import {
  LARGO_DNI,
  MAX_APELLIDO,
  MAX_NOMBRE,
  soloDigitos,
  soloLetras,
} from '../../services/fieldRules'
import type { ProfileForm } from './profileSchema'

interface ProfileFieldsProps {
  readonly register: UseFormRegister<ProfileForm>
  readonly control: Control<ProfileForm>
  readonly errors: FieldErrors<ProfileForm>
}

export default function ProfileFields({ register, control, errors }: ProfileFieldsProps) {
  return (
    <>
      <div className="grid items-start gap-5 sm:grid-cols-2">
        <TextField
          id="first_name"
          label="Nombre"
          placeholder="María"
          icon="perfil"
          autoComplete="given-name"
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
          autoComplete="family-name"
          maxLength={MAX_APELLIDO}
          sanitize={soloLetras}
          field={register('last_name')}
          error={errors.last_name?.message}
        />
        <PhoneField
          id="phone"
          label="Teléfono"
          control={control}
          name="phone"
          error={errors.phone?.message}
        />
        <TextField
          id="document_id"
          label="DNI"
          placeholder="12345678"
          icon="documento"
          inputMode="numeric"
          autoComplete="off"
          maxLength={LARGO_DNI}
          sanitize={soloDigitos}
          field={register('document_id')}
          error={errors.document_id?.message}
        />
      </div>
      <PasswordField
        id="new_password"
        label="Nueva contraseña"
        placeholder="Déjala vacía para no cambiarla"
        autoComplete="new-password"
        hint="Déjala vacía para conservar la actual."
        field={register('new_password')}
        error={errors.new_password?.message}
      />
    </>
  )
}
