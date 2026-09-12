import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation } from '@tanstack/react-query'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { fileComplaint } from '../../api/complaints'
import FieldError from '../../components/FieldError'
import FormMessage from '../../components/FormMessage'
import { onSubmit } from '../../hooks/formSubmit'
import { errorMessage } from '../../services/api'
import EvidenceUploader from './EvidenceUploader'

const esquema = z.object({
  description: z.string().min(1, 'Contanos qué pasó'),
})

type Formulario = z.infer<typeof esquema>

interface ComplaintFormProps {
  readonly appointmentId: number
}

/** Presentar un reclamo sobre una cita propia, con evidencia opcional. */
export default function ComplaintForm({ appointmentId }: ComplaintFormProps) {
  const [complaintId, setComplaintId] = useState<number | null>(null)
  const { register, handleSubmit, formState } = useForm<Formulario>({
    resolver: zodResolver(esquema),
    defaultValues: { description: '' },
  })

  const presentar = useMutation({
    mutationFn: (valores: Formulario) => fileComplaint(appointmentId, valores.description),
    onSuccess: (reclamo) => {
      setComplaintId(reclamo.id)
    },
  })

  if (complaintId !== null) {
    return (
      <div className="stack">
        <FormMessage tone="ok">
          Reclamo presentado. Administración lo va a revisar lo antes posible.
        </FormMessage>
        <EvidenceUploader complaintId={complaintId} />
      </div>
    )
  }

  return (
    <form
      className="form"
      onSubmit={onSubmit(
        handleSubmit((valores) => {
          presentar.mutate(valores)
        }),
      )}
    >
      <div className="field">
        <label htmlFor="description">¿Qué pasó?</label>
        <textarea id="description" rows={3} {...register('description')} />
        <FieldError message={formState.errors.description?.message} />
      </div>

      {presentar.isError ? (
        <FormMessage tone="error">
          {errorMessage(presentar.error, 'No se pudo presentar el reclamo.')}
        </FormMessage>
      ) : null}

      <button type="submit" className="btn btn-danger" disabled={presentar.isPending}>
        <span>{presentar.isPending ? 'Enviando…' : 'Presentar reclamo'}</span>
      </button>
    </form>
  )
}
