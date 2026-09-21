import { type Control, useController } from 'react-hook-form'
import { Link } from 'react-router'

import FieldError from '../../components/FieldError'
import { Checkbox } from '../../components/ui/checkbox'
import { Label } from '../../components/ui/label'
import type { RegisterForm } from './registerSchema'

const ID = 'accepts_terms'
const ID_ERROR = `${ID}-error`

interface TermsConsentFieldProps {
  readonly control: Control<RegisterForm>
  readonly error?: string
}

/**
 * La aceptación de términos y condiciones.
 *
 * Igual que la autorización de DNI: no viene marcada, y sin ella el
 * registro no se envía.
 */
export default function TermsConsentField({ control, error }: TermsConsentFieldProps) {
  const {
    field: { value, onChange, onBlur, ref },
  } = useController({ control, name: 'accepts_terms' })

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
          Acepto los{' '}
          <Link
            to="/terminos"
            target="_blank"
            rel="noreferrer"
            className="rounded-sm font-medium text-primary underline underline-offset-4 outline-none focus-visible:ring-3 focus-visible:ring-ring/50"
          >
            términos y condiciones
            <span className="sr-only"> (se abre en una pestaña nueva)</span>
          </Link>{' '}
          y la{' '}
          <Link
            to="/terminos#privacidad"
            target="_blank"
            rel="noreferrer"
            className="rounded-sm font-medium text-primary underline underline-offset-4 outline-none focus-visible:ring-3 focus-visible:ring-ring/50"
          >
            política de privacidad
            <span className="sr-only"> (se abre en una pestaña nueva)</span>
          </Link>
          .
        </Label>
      </div>
      <FieldError id={ID_ERROR} message={error} />
    </div>
  )
}
