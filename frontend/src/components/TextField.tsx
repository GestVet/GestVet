import type { HTMLInputTypeAttribute } from 'react'
import type { UseFormRegisterReturn } from 'react-hook-form'

import FieldError from './FieldError'
import FieldHint from './FieldHint'
import { fieldIds } from './fieldIds'
import { Input } from './ui/input'
import { Label } from './ui/label'

interface TextFieldProps {
  readonly id: string
  readonly label: string
  /** Lo que devuelve `register(...)` de react-hook-form. */
  readonly field: UseFormRegisterReturn
  readonly type?: HTMLInputTypeAttribute
  readonly error?: string
  readonly hint?: string
  readonly placeholder?: string
  readonly autoComplete?: string
  readonly inputMode?: 'tel' | 'text' | 'email' | 'numeric' | 'decimal'
  readonly maxLength?: number
  readonly step?: string
  readonly min?: string
  readonly accept?: string
}

/**
 * Un campo de texto con su etiqueta, su error y su ayuda.
 *
 * Los formularios repetian el mismo bloque de cuatro lineas por campo.
 * Reunirlo aca es lo que los mantiene por debajo del limite de tamano, y hace
 * que cambiar como se ve un error sea editar un archivo.
 */
export default function TextField({
  id,
  label,
  field,
  type = 'text',
  error,
  hint,
  ...inputProps
}: TextFieldProps) {
  const ids = fieldIds(id, hint, error)

  return (
    <div className="flex flex-col gap-2">
      <Label htmlFor={id}>{label}</Label>
      <Input
        id={id}
        type={type}
        className="h-10"
        aria-invalid={error !== undefined}
        aria-describedby={ids.describedBy}
        {...inputProps}
        {...field}
      />
      <FieldHint id={ids.hintId} hint={hint} />
      <FieldError id={ids.errorId} message={error} />
    </div>
  )
}
