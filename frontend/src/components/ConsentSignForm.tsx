import type { ReactNode } from 'react'
import { Controller } from 'react-hook-form'

import { onSubmit } from '../hooks/formSubmit'
import { useConsentSignForm } from '../hooks/useConsentSignForm'
import ConsentCheckboxField from './ConsentCheckboxField'
import FormMessage from './FormMessage'
import TextField from './TextField'
import { Button } from './ui/button'

interface ConsentSignFormProps {
  readonly id: string
  /** El nombre de la sesión, si firma el titular de la cuenta; se puede corregir. */
  readonly defaultSignerName: string
  readonly checkboxLabel: string
  readonly submitLabel: string
  readonly isPending: boolean
  readonly error?: string
  readonly onSign: (signerName: string) => void
  /** Botones que van junto al de firmar, como "Cancelar". */
  readonly children?: ReactNode
}

/**
 * La firma de un consentimiento: la casilla y el nombre completo.
 *
 * La misma para quien acepta desde su cuenta y para quien firma en la
 * pantalla del veterinario. El texto se muestra aparte, arriba del formulario.
 */
export default function ConsentSignForm({
  id,
  defaultSignerName,
  checkboxLabel,
  submitLabel,
  isPending,
  error,
  onSign,
  children,
}: ConsentSignFormProps) {
  const { form, maxSignerLength } = useConsentSignForm(defaultSignerName)
  const { register, control, handleSubmit, formState } = form

  return (
    <form
      noValidate
      className="flex flex-col gap-4"
      onSubmit={onSubmit(
        handleSubmit((valores) => {
          onSign(valores.signer_name)
        }),
      )}
    >
      <Controller
        control={control}
        name="accepted"
        render={({ field }) => (
          <ConsentCheckboxField
            id={`${id}-acepto`}
            label={checkboxLabel}
            checked={field.value}
            onCheckedChange={field.onChange}
            onBlur={field.onBlur}
            inputRef={field.ref}
            error={formState.errors.accepted?.message}
          />
        )}
      />
      <TextField
        id={`${id}-firma`}
        label="Nombre completo de quien firma"
        icon="perfil"
        autoComplete="name"
        maxLength={maxSignerLength}
        field={register('signer_name')}
        error={formState.errors.signer_name?.message}
      />
      {error === undefined ? null : <FormMessage tone="error">{error}</FormMessage>}
      <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
        {children}
        <Button type="submit" variant="success" disabled={isPending}>
          {isPending ? 'Firmando…' : submitLabel}
        </Button>
      </div>
    </form>
  )
}
