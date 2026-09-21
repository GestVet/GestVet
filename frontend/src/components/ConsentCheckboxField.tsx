import type { Ref } from 'react'

import FieldError from './FieldError'
import { Checkbox } from './ui/checkbox'
import { Label } from './ui/label'

interface ConsentCheckboxFieldProps {
  readonly id: string
  readonly label: string
  readonly checked: boolean
  readonly onCheckedChange: (checked: boolean) => void
  readonly onBlur?: () => void
  readonly inputRef?: Ref<HTMLButtonElement>
  readonly error?: string
}

/**
 * La casilla con la que alguien acepta un texto.
 *
 * Nunca viene marcada: marcarla es el acto de aceptar. Controlada desde
 * afuera para que cada formulario la enlace con su propio `Controller`.
 */
export default function ConsentCheckboxField({
  id,
  label,
  checked,
  onCheckedChange,
  onBlur,
  inputRef,
  error,
}: ConsentCheckboxFieldProps) {
  const idError = `${id}-error`

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-start gap-2.5">
        <Checkbox
          id={id}
          ref={inputRef}
          checked={checked}
          onBlur={onBlur}
          onCheckedChange={(marcado) => {
            onCheckedChange(marcado === true)
          }}
          aria-invalid={error !== undefined}
          aria-describedby={error === undefined ? undefined : idError}
        />
        <Label htmlFor={id} className="cursor-pointer leading-snug font-medium">
          {label}
        </Label>
      </div>
      <FieldError id={idError} message={error} />
    </div>
  )
}
