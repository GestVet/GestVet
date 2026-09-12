import type { HTMLInputTypeAttribute } from 'react'
import type { UseFormRegisterReturn } from 'react-hook-form'

import FieldError from './FieldError'
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
  readonly inputMode?: 'tel' | 'text' | 'email' | 'numeric'
  readonly maxLength?: number
}

/**
 * Un campo de texto con su etiqueta, su error y su ayuda.
 *
 * Los seis formularios repetian el mismo bloque de cuatro lineas por campo.
 * Reunirlo aca es lo que los mantiene por debajo del limite de tamano, y hace
 * que cambiar como se ve un error sea editar un archivo.
 *
 * La ayuda y el error quedan enlazados al campo con `aria-describedby`: quien
 * usa lector de pantalla los oye al entrar al campo, no solo quien los ve.
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
  maxLength,
}: TextFieldProps) {
  const hintId = `${id}-ayuda`
  const errorId = `${id}-error`
  const describedBy = [hint === undefined ? '' : hintId, error === undefined ? '' : errorId]
    .filter((value) => value !== '')
    .join(' ')

  return (
    <div className="flex flex-col gap-2">
      <Label htmlFor={id}>{label}</Label>
      <Input
        id={id}
        type={type}
        className="h-10"
        placeholder={placeholder}
        autoComplete={autoComplete}
        inputMode={inputMode}
        maxLength={maxLength}
        aria-invalid={error !== undefined}
        aria-describedby={describedBy === '' ? undefined : describedBy}
        {...field}
      />
      {hint === undefined ? null : (
        <p id={hintId} className="m-0 text-sm text-muted-foreground">
          {hint}
        </p>
      )}
      <FieldError id={errorId} message={error} />
    </div>
  )
}
