import type { FieldErrors, UseFormRegister } from 'react-hook-form'

import PasswordField from '../../components/PasswordField'
import TextField from '../../components/TextField'
import {
  LARGO_DNI,
  MAX_APELLIDO,
  MAX_NOMBRE,
  MAX_TELEFONO,
  MIN_PASSWORD,
  soloDigitos,
  soloLetras,
  soloTelefono,
} from '../../services/fieldRules'
import type { RegisterForm } from './registerSchema'

interface RegisterFieldsProps {
  readonly register: UseFormRegister<RegisterForm>
  readonly errors: FieldErrors<RegisterForm>
}

/**
 * Los campos del registro.
 *
 * En pantalla ancha nombre y apellido, y telefono y DNI, van de a pares: son
 * datos cortos y la tarjeta queda a la mitad de alto. En celular se apilan.
 * Nombre, DNI y telefono se limpian mientras se escribe, asi un numero en el
 * nombre o una letra en el DNI no llegan a mostrarse como error.
 */
export default function RegisterFields({ register, errors }: RegisterFieldsProps) {
  return (
    <>
      <div className="grid gap-5 sm:grid-cols-2">
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
      </div>

      <TextField
        id="email"
        label="Correo"
        type="email"
        inputMode="email"
        autoComplete="email"
        spellCheck={false}
        field={register('email')}
        error={errors.email?.message}
      />

      <div className="grid items-start gap-5 sm:grid-cols-2">
        <TextField
          id="document_id"
          label="DNI"
          inputMode="numeric"
          autoComplete="off"
          maxLength={LARGO_DNI}
          hint="8 dígitos, sin puntos."
          sanitize={soloDigitos}
          field={register('document_id')}
          error={errors.document_id?.message}
        />
        <TextField
          id="phone"
          label="Teléfono (opcional)"
          type="tel"
          inputMode="tel"
          autoComplete="tel"
          maxLength={MAX_TELEFONO}
          hint="Por ejemplo, 987 654 321."
          sanitize={soloTelefono}
          field={register('phone')}
          error={errors.phone?.message}
        />
      </div>

      <PasswordField
        id="password"
        label="Contraseña"
        autoComplete="new-password"
        hint={`Al menos ${String(MIN_PASSWORD)} caracteres.`}
        field={register('password')}
        error={errors.password?.message}
      />
    </>
  )
}
