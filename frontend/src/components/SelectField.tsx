import type { ReactNode } from 'react'
import type { UseFormRegisterReturn } from 'react-hook-form'

import FieldError from './FieldError'

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

export default function SelectField({
  id,
  label,
  field,
  error,
  hint,
  placeholder,
  children,
}: SelectFieldProps) {
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <select id={id} {...field}>
        {placeholder === undefined ? null : <option value="">{placeholder}</option>}
        {children}
      </select>
      {hint === undefined ? null : <span className="muted">{hint}</span>}
      <FieldError message={error} />
    </div>
  )
}
