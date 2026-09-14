import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { submitReview } from '../../api/reviews'
import FormMessage from '../../components/FormMessage'
import { textoObligatorio } from '../../components/formRules'
import Icon from '../../components/Icon'
import SelectField from '../../components/SelectField'
import TextareaField from '../../components/TextareaField'
import { Button } from '../../components/ui/button'
import { NativeSelectOption } from '../../components/ui/native-select'
import { onSubmit } from '../../hooks/formSubmit'
import { errorMessage } from '../../services/api'

const esquema = z.object({
  rating: z.enum(['1', '2', '3', '4', '5']),
  comment: textoObligatorio(500, 'Cuéntanos cómo fue la atención'),
})

type Formulario = z.infer<typeof esquema>

const VACIO: Formulario = { rating: '5', comment: '' }

interface ReviewFormProps {
  readonly appointmentId: number
  readonly veterinarianId: number
}

/** Calificar al veterinario que atendió esta cita. Volver a enviarlo actualiza la reseña. */
export default function ReviewForm({ appointmentId, veterinarianId }: ReviewFormProps) {
  const { register, handleSubmit, reset, formState } = useForm<Formulario>({
    resolver: zodResolver(esquema),
    defaultValues: VACIO,
  })
  const campo = (nombre: string) => `${nombre}-${String(appointmentId)}`

  const enviar = useMutation({
    mutationFn: (valores: Formulario) =>
      submitReview({
        veterinarian_id: veterinarianId,
        rating: Number(valores.rating),
        comment: valores.comment,
      }),
    onSuccess: () => {
      reset(VACIO)
    },
  })

  return (
    <form
      noValidate
      className="flex flex-col gap-4"
      onSubmit={onSubmit(
        handleSubmit((valores) => {
          enviar.mutate(valores)
        }),
      )}
    >
      <div className="max-w-xs">
        <SelectField id={campo('rating')} label="Calificación" icon="estrella" field={register('rating')}>
          <NativeSelectOption value="5">★★★★★ (5)</NativeSelectOption>
          <NativeSelectOption value="4">★★★★ (4)</NativeSelectOption>
          <NativeSelectOption value="3">★★★ (3)</NativeSelectOption>
          <NativeSelectOption value="2">★★ (2)</NativeSelectOption>
          <NativeSelectOption value="1">★ (1)</NativeSelectOption>
        </SelectField>
      </div>

      <TextareaField
        id={campo('comment')}
        label="Comentario"
        icon="mensaje"
        rows={2}
        field={register('comment')}
        error={formState.errors.comment?.message}
      />

      {enviar.isError ? (
        <FormMessage tone="error">
          {errorMessage(enviar.error, 'No se pudo enviar la reseña.')}
        </FormMessage>
      ) : null}
      {enviar.isSuccess ? <FormMessage tone="ok">¡Gracias por tu reseña!</FormMessage> : null}

      <Button type="submit" variant="success" className="self-start" disabled={enviar.isPending}>
        <Icon name="confirmar" size={16} />
        <span>{enviar.isPending ? 'Enviando…' : 'Enviar reseña'}</span>
      </Button>
    </form>
  )
}
