import type { Control, FieldErrors, UseFormRegister } from 'react-hook-form'

import PasswordField from '../../components/PasswordField'
import PhoneField from '../../components/PhoneField'
import TextField from '../../components/TextField'
import { soloLetras } from '../../services/fieldRules'
import type { StaffFormValues } from './staffSchema'

interface StaffFieldsProps {
  readonly register: UseFormRegister<StaffFormValues>
  readonly control: Control<StaffFormValues>
  readonly errors: FieldErrors<StaffFormValues>
}

export default function StaffFields({ register, control, errors }: StaffFieldsProps) {
  return (
    <div className="grid gap-5 sm:grid-cols-2">
      <TextField
        id="first_name"
        label="Nombre"
        placeholder="Por ejemplo: María"
        icon="perfil"
        sanitize={soloLetras}
        field={register('first_name')}
        error={errors.first_name?.message}
      />
      <TextField
        id="last_name"
        label="Apellido"
        placeholder="Por ejemplo: Quispe Rojas"
        icon="perfil"
        sanitize={soloLetras}
        field={register('last_name')}
        error={errors.last_name?.message}
      />
      <TextField
        id="email"
        label="Correo"
        placeholder="nombre@correo.com"
        type="email"
        field={register('email')}
        error={errors.email?.message}
      />
      <PhoneField
        id="phone"
        label="Teléfono"
        control={control}
        name="phone"
        error={errors.phone?.message}
      />
      <PasswordField
        id="password"
        label="Contraseña inicial"
        placeholder="Mínimo 10 caracteres"
        autoComplete="new-password"
        hint="Al menos 10 caracteres."
        field={register('password')}
        error={errors.password?.message}
      />
    </div>
  )
}
