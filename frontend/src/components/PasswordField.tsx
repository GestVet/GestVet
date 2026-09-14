import { useState } from 'react'
import type { UseFormRegisterReturn } from 'react-hook-form'

import FieldError from './FieldError'
import FieldHint from './FieldHint'
import FieldIcon from './FieldIcon'
import { fieldIds } from './fieldIds'
import Icon from './Icon'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { Label } from './ui/label'

interface PasswordFieldProps {
  readonly id: string
  readonly label: string
  /** Lo que devuelve `register(...)` de react-hook-form. */
  readonly field: UseFormRegisterReturn
  readonly autoComplete: 'current-password' | 'new-password'
  readonly error?: string
  readonly hint?: string
  readonly placeholder?: string
}

/**
 * Un campo de contrasena con un boton para verla.
 *
 * En el celular una contrasena larga se escribe mal a ciegas, y la regla de
 * diez caracteres hace que equivocarse cueste. El boton cambia su nombre
 * accesible segun el estado, asi el lector de pantalla anuncia que hara.
 */
export default function PasswordField({
  id,
  label,
  field,
  autoComplete,
  error,
  hint,
  placeholder,
}: PasswordFieldProps) {
  const [visible, setVisible] = useState(false)
  const ids = fieldIds(id, hint, error)

  return (
    <div className="flex flex-col gap-2">
      <Label htmlFor={id}>{label}</Label>
      <FieldIcon icon="candado">
        <Input
          id={id}
          type={visible ? 'text' : 'password'}
          className="h-10 pr-11"
          autoComplete={autoComplete}
          spellCheck={false}
          placeholder={placeholder}
          aria-invalid={error !== undefined}
          aria-describedby={ids.describedBy}
          {...field}
        />
        <div className="absolute inset-y-0 right-1.5 flex items-center">
          <Button
            type="button"
            variant="ghost"
            size="icon-sm"
            className="text-muted-foreground"
            aria-controls={id}
            aria-label={visible ? 'Ocultar contraseña' : 'Mostrar contraseña'}
            onClick={() => {
              setVisible((actual) => !actual)
            }}
          >
            <Icon name={visible ? 'ocultar' : 'ver'} size={18} />
          </Button>
        </div>
      </FieldIcon>
      <FieldHint id={ids.hintId} hint={hint} />
      <FieldError id={ids.errorId} message={error} />
    </div>
  )
}
