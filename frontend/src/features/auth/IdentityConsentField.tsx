import { type Control, useController } from 'react-hook-form'

import FieldError from '../../components/FieldError'
import { Checkbox } from '../../components/ui/checkbox'
import { Label } from '../../components/ui/label'
import type { RegisterForm } from './registerSchema'

const ID = 'accepts_identity_check'
const ID_ERROR = `${ID}-error`

interface IdentityConsentFieldProps {
  readonly control: Control<RegisterForm>
  readonly error?: string
}

/**
 * La autorización para verificar el DNI.
 *
 * Consultar un DNI es tratar un dato personal, así que se pide de forma
 * explícita y no viene marcada. Sin ella el registro no se envía.
 */
export default function IdentityConsentField({ control, error }: IdentityConsentFieldProps) {
  const {
    field: { value, onChange, onBlur, ref },
  } = useController({ control, name: 'accepts_identity_check' })

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-start gap-2.5">
        <Checkbox
          id={ID}
          ref={ref}
          checked={value}
          onBlur={onBlur}
          onCheckedChange={(marcado) => {
            onChange(marcado === true)
          }}
          aria-invalid={error !== undefined}
          aria-describedby={error === undefined ? undefined : ID_ERROR}
        />
        <Label htmlFor={ID} className="cursor-pointer leading-snug font-normal text-muted-foreground">
          Autorizo a la clínica a verificar mi DNI para confirmar mi identidad. Solo se comprueba
          que el nombre coincida.
        </Label>
      </div>
      <FieldError id={ID_ERROR} message={error} />
    </div>
  )
}
