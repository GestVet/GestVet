import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { onSubmit } from '../hooks/formSubmit'
import { useAddHospitalizationNote } from '../hooks/useHospitalizations'
import FormMessage from './FormMessage'
import { MIN_TEXTO, textoObligatorio } from './formRules'
import TextareaField from './TextareaField'
import { Button } from './ui/button'

// El mismo tope que el servidor.
const MAX_NOTA = 1000

const esquema = z.object({ nota: textoObligatorio(MAX_NOTA, 'Escribe la nota') })

type Formulario = z.infer<typeof esquema>

const VACIO: Formulario = { nota: '' }

interface HospitalizationNoteFormProps {
  readonly hospitalizationId: number
  readonly petId: number
}

/** Una nota de seguimiento de la internación. */
export default function HospitalizationNoteForm({
  hospitalizationId,
  petId,
}: HospitalizationNoteFormProps) {
  const agregarNota = useAddHospitalizationNote(petId)
  const { register, handleSubmit, reset, formState } = useForm<Formulario>({
    resolver: zodResolver(esquema),
    defaultValues: VACIO,
  })

  return (
    <form
      noValidate
      className="flex flex-col gap-2"
      onSubmit={onSubmit(
        handleSubmit((valores) => {
          agregarNota.mutate(
            { hospitalizationId, note: valores.nota },
            {
              onSuccess: () => {
                reset(VACIO)
              },
            },
          )
        }),
      )}
    >
      <TextareaField
        id={`nota-${String(hospitalizationId)}`}
        label="Nota de seguimiento"
        icon="nota"
        rows={2}
        maxLength={MAX_NOTA}
        placeholder="Por ejemplo: come bien, sin fiebre, se retira el suero"
        hint={`Entre ${String(MIN_TEXTO)} y ${String(MAX_NOTA)} caracteres.`}
        field={register('nota')}
        error={formState.errors.nota?.message}
      />
      {agregarNota.isError ? (
        <FormMessage tone="error">{agregarNota.errorMessage}</FormMessage>
      ) : null}
      <Button type="submit" variant="outline" className="self-start" disabled={agregarNota.isPending}>
        {agregarNota.isPending ? 'Agregando…' : 'Agregar nota'}
      </Button>
    </form>
  )
}
