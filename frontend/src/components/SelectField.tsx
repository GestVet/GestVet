import type { ReactNode } from 'react'
import type { UseFormRegisterReturn } from 'react-hook-form'

import FieldError from './FieldError'
import FieldHint from './FieldHint'
import { fieldIds } from './fieldIds'
import { Label } from './ui/label'
import { NativeSelect, NativeSelectOption } from './ui/native-select'

interface SelectFieldProps {
  readonly id: string
  readonly label: string
  /** Lo que devuelve `register(...)` de react-hook-form. */
  readonly field: UseFormRegisterReturn
  readonly error?: string
  readonly hint?: string
  /** Texto de la opcion vacia. Sin el, la lista no ofrece "ninguna". */
  readonly placeholder?: string
  readonly children: ReactNode
}

/**
 * Una lista desplegable con su etiqueta, su error y su ayuda.
 *
 * Usa el select nativo de shadcn y no el de Radix: se registra con
 * react-hook-form igual que un campo de texto, y en el celular abre la lista
 * del sistema, que es la que la persona ya sabe usar.
 */
export default function SelectField({
  id,
  label,
  field,
  error,
  hint,
  placeholder,
  children,
}: SelectFieldProps) {
  const ids = fieldIds(id, hint, error)

  return (
    <div className="flex flex-col gap-2">
      <Label htmlFor={id}>{label}</Label>
      <NativeSelect
        id={id}
        className="w-full [&_select]:h-10"
        aria-invalid={error !== undefined}
        aria-describedby={ids.describedBy}
        {...field}
      >
        {placeholder === undefined ? null : (
          <NativeSelectOption value="">{placeholder}</NativeSelectOption>
        )}
        {children}
      </NativeSelect>
      <FieldHint id={ids.hintId} hint={hint} />
      <FieldError id={ids.errorId} message={error} />
    </div>
  )
}
