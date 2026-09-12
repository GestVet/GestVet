import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { submitReview } from '../../api/reviews'
import FieldError from '../../components/FieldError'
import FormMessage from '../../components/FormMessage'
import Icon from '../../components/Icon'
import SelectField from '../../components/SelectField'
import { onSubmit } from '../../hooks/formSubmit'
import { errorMessage } from '../../services/api'

const esquema = z.object({
  rating: z.enum(['1', '2', '3', '4', '5']),
  comment: z.string().min(1, 'Contanos cómo fue la atención'),
})

type Formulario = z.infer<typeof esquema>

const VACIO: Formulario = { rating: '5', comment: '' }

interface ReviewFormProps {
  readonly veterinarianId: number
}

/** Calificar al veterinario que atendió esta cita. Volver a enviarlo actualiza la reseña. */
export default function ReviewForm({ veterinarianId }: ReviewFormProps) {
  const { register, handleSubmit, reset, formState } = useForm<Formulario>({
    resolver: zodResolver(esquema),
    defaultValues: VACIO,
  })

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
      className="form"
      onSubmit={onSubmit(
        handleSubmit((valores) => {
          enviar.mutate(valores)
        }),
      )}
    >
      <SelectField id="rating" label="Calificación" field={register('rating')}>
        <option value="5">★★★★★ (5)</option>
        <option value="4">★★★★ (4)</option>
        <option value="3">★★★ (3)</option>
        <option value="2">★★ (2)</option>
        <option value="1">★ (1)</option>
      </SelectField>

      <div className="field">
        <label htmlFor="comment">Comentario</label>
        <textarea id="comment" rows={2} {...register('comment')} />
        <FieldError message={formState.errors.comment?.message} />
      </div>

      {enviar.isError ? (
        <FormMessage tone="error">
          {errorMessage(enviar.error, 'No se pudo enviar la reseña.')}
        </FormMessage>
      ) : null}
      {enviar.isSuccess ? <FormMessage tone="ok">¡Gracias por tu reseña!</FormMessage> : null}

      <button type="submit" className="btn btn-green" disabled={enviar.isPending}>
        <Icon name="confirmar" size={16} />
        <span>{enviar.isPending ? 'Enviando…' : 'Enviar reseña'}</span>
      </button>
    </form>
  )
}
