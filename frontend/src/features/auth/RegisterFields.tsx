import type { Control, FieldErrors, UseFormRegister } from 'react-hook-form'

import PasswordField from '../../components/PasswordField'
import PhoneField from '../../components/PhoneField'
import TextField from '../../components/TextField'
import {
  LARGO_DNI,
  MAX_APELLIDO,
  MAX_NOMBRE,
  MIN_PASSWORD,
  soloDigitos,
  soloLetras,
} from '../../services/fieldRules'
import type { RegisterForm } from './registerSchema'

interface RegisterFieldsProps {
  readonly register: UseFormRegister<RegisterForm>
  readonly control: Control<RegisterForm>
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
export default function RegisterFields({ register, control, errors }: RegisterFieldsProps) {
  return (
    <>
      <div className="grid gap-5 sm:grid-cols-2">
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
      </div>

      <TextField
        id="email"
        label="Correo"
        placeholder="nombre@correo.com"
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
          placeholder="12345678"
          icon="documento"
          inputMode="numeric"
          autoComplete="off"
          maxLength={LARGO_DNI}
          hint="8 dígitos, sin puntos."
          sanitize={soloDigitos}
          field={register('document_id')}
          error={errors.document_id?.message}
        />
        <PhoneField
          id="phone"
          label="Teléfono (opcional)"
          control={control}
          name="phone"
          error={errors.phone?.message}
        />
      </div>

      <PasswordField
        id="password"
        label="Contraseña"
        placeholder="Mínimo 10 caracteres"
        autoComplete="new-password"
        hint={`Al menos ${String(MIN_PASSWORD)} caracteres.`}
        field={register('password')}
        error={errors.password?.message}
      />
    </>
  )
}
