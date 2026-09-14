import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { onSubmit } from '../hooks/formSubmit'
import { useDischargeHospitalization } from '../hooks/useHospitalizations'
import FormMessage from './FormMessage'
import { textoOpcional } from './formRules'
import TextareaField from './TextareaField'
import { Button } from './ui/button'

// El mismo tope que el servidor.
const MAX_NOTAS = 1000

const esquema = z.object({ notas: textoOpcional(MAX_NOTAS) })

type Formulario = z.infer<typeof esquema>

interface HospitalizationDischargeFormProps {
  readonly hospitalizationId: number
  readonly petId: number
}

/** El alta de la internación, con indicaciones opcionales. */
export default function HospitalizationDischargeForm({
  hospitalizationId,
  petId,
}: HospitalizationDischargeFormProps) {
  const darDeAlta = useDischargeHospitalization(petId)
  const { register, handleSubmit, formState } = useForm<Formulario>({
    resolver: zodResolver(esquema),
    defaultValues: { notas: '' },
  })

  return (
    <form
      noValidate
      className="flex flex-col gap-2"
      onSubmit={onSubmit(
        handleSubmit((valores) => {
          darDeAlta.mutate({ hospitalizationId, dischargeNotes: valores.notas })
        }),
      )}
    >
      <TextareaField
        id={`alta-${String(hospitalizationId)}`}
        label="Notas de alta (opcional)"
        icon="nota"
        rows={2}
        maxLength={MAX_NOTAS}
        placeholder="Indicaciones para la casa y controles pendientes"
        field={register('notas')}
        error={formState.errors.notas?.message}
      />
      {darDeAlta.isError ? <FormMessage tone="error">{darDeAlta.errorMessage}</FormMessage> : null}
      <Button type="submit" variant="success" className="self-start" disabled={darDeAlta.isPending}>
        {darDeAlta.isPending ? 'Dando de alta…' : 'Dar de alta'}
      </Button>
    </form>
  )
}
