import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { openHospitalization } from '../../api/hospitalizations'
import FormMessage from '../../components/FormMessage'
import { textoObligatorio } from '../../components/formRules'
import TextareaField from '../../components/TextareaField'
import { Button } from '../../components/ui/button'
import { onSubmit } from '../../hooks/formSubmit'
import { errorMessage, errorStatus } from '../../services/api'

// El servidor responde 409 cuando falta el consentimiento de internación.
const SIN_CONSENTIMIENTO = 409

const esquema = z.object({
  reason: textoObligatorio(300, 'Cuenta por qué queda internada'),
})

type Formulario = z.infer<typeof esquema>

interface OpenHospitalizationFormProps {
  readonly appointmentId: number
  /** Lleva a pedir el consentimiento de internación cuando falta. */
  readonly onRequestConsent: () => void
}

/** Abrir una internación a partir de una cita ya atendida. Solo lo hace un veterinario. */
export default function OpenHospitalizationForm({
  appointmentId,
  onRequestConsent,
}: OpenHospitalizationFormProps) {
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
        Internación abierta. Puedes agregar notas de seguimiento desde la ficha de la mascota.
      </FormMessage>
    )
  }

  return (
    <form
      noValidate
      className="flex flex-col gap-4"
      onSubmit={onSubmit(
        handleSubmit((valores) => {
          abrir.mutate(valores)
        }),
      )}
    >
      <TextareaField
        id={`internacion-${String(appointmentId)}`}
        label="Motivo de la internación"
        placeholder="Deshidratación, necesita suero y observación"
        icon="nota"
        rows={2}
        field={register('reason')}
        error={formState.errors.reason?.message}
      />

      {abrir.isError ? (
        <FormMessage tone="error">
          {errorMessage(abrir.error, 'No se pudo abrir la internación.')}
        </FormMessage>
      ) : null}
      {errorStatus(abrir.error) === SIN_CONSENTIMIENTO ? (
        <Button type="button" variant="outline" className="self-start" onClick={onRequestConsent}>
          Solicitar el consentimiento de internación
        </Button>
      ) : null}

      <Button type="submit" variant="success" className="self-start" disabled={abrir.isPending}>
        {abrir.isPending ? 'Abriendo…' : 'Internar'}
      </Button>
    </form>
  )
}
