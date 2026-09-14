import { lazy, Suspense, useState } from 'react'
import { type Control, type FieldPathByValue, type FieldValues, useController } from 'react-hook-form'

import CountryCodePlaceholder from './CountryCodePlaceholder'
import FieldError from './FieldError'
import FieldHint from './FieldHint'
import { fieldIds } from './fieldIds'
import { paisPorIso, separarTelefono, soloNumeroNacional, unirTelefono } from './phoneCountries'
import { Input } from './ui/input'
import { Label } from './ui/label'

// Las banderas de 245 países pesan: el selector se baja aparte, así no
// engordan la carga de las páginas que no piden un teléfono.
const CountryCodeSelect = lazy(() => import('./CountryCodeSelect'))

// Quince dígitos es el tope de un número internacional, más los espacios.
const MAX_NUMERO = 18

interface PhoneFieldProps<TForm extends FieldValues> {
  readonly id: string
  readonly label: string
  readonly control: Control<TForm>
  readonly name: FieldPathByValue<TForm, string>
  readonly error?: string
  readonly hint?: string
}

/**
 * Un teléfono con su código de país.
 *
 * El formulario guarda un solo texto, "+51 987 654 321", igual que antes: el
 * selector y el número son dos mitades de ese valor. Mientras el número está
 * vacío el campo queda vacío, así un teléfono opcional sigue siendo opcional
 * aunque se haya elegido un país.
 */
export default function PhoneField<TForm extends FieldValues>({
  id,
  label,
  control,
  name,
  error,
  hint,
}: PhoneFieldProps<TForm>) {
  const {
    field: { value, onChange, onBlur, ref },
  } = useController({ control, name })
  const valor: string = value
  const [paisElegido, setPaisElegido] = useState(() => separarTelefono(valor).iso)
  const partes = separarTelefono(valor, paisElegido)
  const iso = valor === '' ? paisElegido : partes.iso
  const ids = fieldIds(id, hint, error)

  return (
    <div className="flex flex-col gap-2">
      <Label htmlFor={id}>{label}</Label>
      <div className="flex">
        <Suspense fallback={<CountryCodePlaceholder iso={iso} />}>
          <CountryCodeSelect
            value={iso}
            invalid={error !== undefined}
            describedBy={ids.describedBy}
            onChange={(nuevo) => {
              setPaisElegido(nuevo)
              onChange(unirTelefono(nuevo, partes.numero))
            }}
          />
        </Suspense>
        <Input
          id={id}
          ref={ref}
          name={name}
          type="tel"
          inputMode="tel"
          autoComplete="tel-national"
          className="-ml-px h-10 rounded-l-none"
          placeholder={paisPorIso(iso).ejemplo}
          maxLength={MAX_NUMERO}
          aria-invalid={error !== undefined}
          aria-describedby={ids.describedBy}
          value={partes.numero}
          onBlur={onBlur}
          onChange={(evento) => {
            onChange(unirTelefono(iso, soloNumeroNacional(evento.target.value)))
          }}
        />
      </div>
      <FieldHint id={ids.hintId} hint={hint} />
      <FieldError id={ids.errorId} message={error} />
    </div>
  )
}
