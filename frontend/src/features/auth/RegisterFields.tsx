import type { FieldErrors, UseFormRegister } from 'react-hook-form'

import TextField from '../../components/TextField'
import { MIN_PASSWORD, type RegisterForm } from './registerSchema'

interface RegisterFieldsProps {
  readonly register: UseFormRegister<RegisterForm>
  readonly errors: FieldErrors<RegisterForm>
}

/**
 * Los campos del registro.
 *
 * En pantalla ancha nombre y apellido, y telefono y DNI, van de a pares: son
 * datos cortos y la tarjeta queda a la mitad de alto. En celular se apilan.
 */
export default function RegisterFields({ register, errors }: RegisterFieldsProps) {
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
      </div>

      <TextField
        id="email"
        label="Correo"
        type="email"
        autoComplete="email"
        field={register('email')}
        error={errors.email?.message}
      />

      <div className="grid gap-5 sm:grid-cols-2">
        <TextField
          id="phone"
          label="Teléfono (opcional)"
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
        id="password"
        label="Contraseña"
        type="password"
        autoComplete="new-password"
        hint={`Al menos ${String(MIN_PASSWORD)} caracteres.`}
        field={register('password')}
        error={errors.password?.message}
      />
    </>
  )
}
