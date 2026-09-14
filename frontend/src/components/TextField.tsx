import type { HTMLInputTypeAttribute } from 'react'
import type { UseFormRegisterReturn } from 'react-hook-form'

import FieldError from './FieldError'
import FieldHint from './FieldHint'
import FieldIcon from './FieldIcon'
import { fieldIds } from './fieldIds'
import type { IconName } from './icons'
import { Input } from './ui/input'
import { Label } from './ui/label'

// El icono que corresponde por el tipo de dato, cuando el campo no pide otro.
const ICONO_POR_TIPO: Readonly<Partial<Record<string, IconName>>> = {
  email: 'correo',
  tel: 'telefono',
  date: 'fecha',
  time: 'horario',
  number: 'numero',
}

interface TextFieldProps {
  readonly id: string
  readonly label: string
  /** Lo que devuelve `register(...)` de react-hook-form. */
  readonly field: UseFormRegisterReturn
  readonly type?: HTMLInputTypeAttribute
  /** Icono a la izquierda. Sin él, se usa el del tipo de dato, si lo hay. */
  readonly icon?: IconName
  readonly error?: string
  readonly hint?: string
  readonly placeholder?: string
  readonly autoComplete?: string
  readonly inputMode?: 'tel' | 'text' | 'email' | 'numeric' | 'decimal'
  readonly maxLength?: number
  readonly step?: string
  readonly min?: string
  readonly max?: string
  readonly accept?: string
  readonly spellCheck?: boolean
  /**
   * Limpia lo que se escribe antes de que llegue al formulario: un DNI que
   * solo acepta digitos, un nombre que no acepta numeros. La regla del esquema
   * sigue validando, porque un valor pegado o autocompletado tambien pasa.
   */
  readonly sanitize?: (valor: string) => string
}

/**
 * Un campo de texto con su etiqueta, su icono, su error y su ayuda.
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
  icon,
  error,
  hint,
  sanitize,
  ...inputProps
}: TextFieldProps) {
  const ids = fieldIds(id, hint, error)
  const { onChange, ...registro } = field

  return (
    <div className="flex flex-col gap-2">
      <Label htmlFor={id}>{label}</Label>
      <FieldIcon icon={icon ?? ICONO_POR_TIPO[type]}>
        <Input
          id={id}
          type={type}
          className="h-10"
          aria-invalid={error !== undefined}
          aria-describedby={ids.describedBy}
          {...inputProps}
          {...registro}
          onChange={(evento) => {
            if (sanitize !== undefined) {
              evento.target.value = sanitize(evento.target.value)
            }
            void onChange(evento)
          }}
        />
      </FieldIcon>
      <FieldHint id={ids.hintId} hint={hint} />
      <FieldError id={ids.errorId} message={error} />
    </div>
  )
}
