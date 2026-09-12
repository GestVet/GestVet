import type { FieldErrors, UseFormRegister } from 'react-hook-form'

import SelectField from '../../components/SelectField'
import TextField from '../../components/TextField'
import { NativeSelectOption } from '../../components/ui/native-select'
import type { StaffFormValues } from './staffSchema'

interface StaffFieldsProps {
  readonly register: UseFormRegister<StaffFormValues>
  readonly errors: FieldErrors<StaffFormValues>
}

export default function StaffFields({ register, errors }: StaffFieldsProps) {
  return (
    <div className="grid gap-5 sm:grid-cols-2">
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
        id="email"
        label="Correo"
        type="email"
        field={register('email')}
        error={errors.email?.message}
      />
      <TextField id="phone" label="Teléfono" type="tel" inputMode="tel" field={register('phone')} />
      <TextField
        id="password"
        label="Contraseña inicial"
        type="password"
        autoComplete="new-password"
        hint="Al menos 10 caracteres."
        field={register('password')}
        error={errors.password?.message}
      />
      <SelectField id="role" label="Rol" field={register('role')}>
        <NativeSelectOption value="veterinarian">Veterinario</NativeSelectOption>
        <NativeSelectOption value="emergency_veterinarian">
          Veterinario de guardia
        </NativeSelectOption>
      </SelectField>
    </div>
  )
}
