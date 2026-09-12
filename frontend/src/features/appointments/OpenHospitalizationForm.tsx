import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { openHospitalization } from '../../api/hospitalizations'
import FieldError from '../../components/FieldError'
import FormMessage from '../../components/FormMessage'
import { onSubmit } from '../../hooks/formSubmit'
import { errorMessage } from '../../services/api'

const esquema = z.object({
  reason: z.string().min(1, 'Contanos por qué queda internada'),
})

type Formulario = z.infer<typeof esquema>

interface OpenHospitalizationFormProps {
  readonly appointmentId: number
}

/** Abrir una internación a partir de una cita ya atendida. Solo lo hace un veterinario. */
export default function OpenHospitalizationForm({ appointmentId }: OpenHospitalizationFormProps) {
  const { register, handleSubmit, reset, formState } = useForm<Formulario>({
    resolver: zodResolver(esquema),
    defaultValues: { reason: '' },
  })

  const abrir = useMutation({
    mutationFn: (valores: Formulario) => openHospitalization(appointmentId, valores.reason),
    onSuccess: () => {
      reset({ reason: '' })
    },
  })

  if (abrir.isSuccess) {
    return (
      <FormMessage tone="ok">
        Internación abierta. Podés agregar notas de seguimiento desde la ficha de la mascota.
      </FormMessage>
    )
  }

  return (
    <form
      className="form"
      onSubmit={onSubmit(
        handleSubmit((valores) => {
          abrir.mutate(valores)
        }),
      )}
    >
      <div className="field">
        <label htmlFor="reason">Motivo de la internación</label>
        <textarea id="reason" rows={2} {...register('reason')} />
        <FieldError message={formState.errors.reason?.message} />
      </div>

      {abrir.isError ? (
        <FormMessage tone="error">
          {errorMessage(abrir.error, 'No se pudo abrir la internación.')}
        </FormMessage>
      ) : null}

      <button type="submit" className="btn btn-green" disabled={abrir.isPending}>
        <span>{abrir.isPending ? 'Abriendo…' : 'Internar'}</span>
      </button>
    </form>
  )
}
