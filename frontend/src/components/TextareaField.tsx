import type { UseFormRegisterReturn } from 'react-hook-form'

import FieldError from './FieldError'
import FieldHint from './FieldHint'
import { fieldIds } from './fieldIds'
import { Label } from './ui/label'
import { Textarea } from './ui/textarea'

interface TextareaFieldProps {
  readonly id: string
  readonly label: string
  /** Lo que devuelve `register(...)` de react-hook-form. */
  readonly field: UseFormRegisterReturn
  readonly error?: string
  readonly hint?: string
  readonly rows?: number
  readonly placeholder?: string
}

/** Un texto largo con su etiqueta, su error y su ayuda. */
export default function TextareaField({
  id,
  label,
  field,
  error,
  hint,
  rows = 3,
  placeholder,
}: TextareaFieldProps) {
  const ids = fieldIds(id, hint, error)

  return (
    <div className="flex flex-col gap-2">
      <Label htmlFor={id}>{label}</Label>
      <Textarea
        id={id}
        rows={rows}
        placeholder={placeholder}
        aria-invalid={error !== undefined}
        aria-describedby={ids.describedBy}
        {...field}
      />
      <FieldHint id={ids.hintId} hint={hint} />
      <FieldError id={ids.errorId} message={error} />
    </div>
  )
}
