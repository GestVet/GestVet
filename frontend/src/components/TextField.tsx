import type { HTMLInputTypeAttribute } from 'react'
import type { UseFormRegisterReturn } from 'react-hook-form'

import FieldError from './FieldError'

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
  readonly inputMode?: 'tel' | 'text' | 'email' | 'numeric'
}

/**
 * Un campo de texto con su etiqueta, su error y su ayuda.
 *
 * Los seis formularios repetian el mismo bloque de cuatro lineas por campo.
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
  placeholder,
  autoComplete,
  inputMode,
}: TextFieldProps) {
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <input
        id={id}
        type={type}
        placeholder={placeholder}
        autoComplete={autoComplete}
        inputMode={inputMode}
        {...field}
      />
      {hint === undefined ? null : <span className="muted">{hint}</span>}
      <FieldError message={error} />
    </div>
  )
}
