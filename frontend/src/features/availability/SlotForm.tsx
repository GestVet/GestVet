import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { mySlotsQueryKey, publishSlot } from '../../api/availability'
import FormMessage from '../../components/FormMessage'
import Icon from '../../components/Icon'
import SectionCard from '../../components/SectionCard'
import TextField from '../../components/TextField'
import { Button } from '../../components/ui/button'
import { onSubmit } from '../../hooks/formSubmit'
import { errorMessage } from '../../services/api'

const esquema = z
  .object({
    starts_at: z.string().min(1, 'Elegí el inicio'),
    ends_at: z.string().min(1, 'Elegí el fin'),
  })
  .refine((valores) => new Date(valores.ends_at) > new Date(valores.starts_at), {
    message: 'El fin tiene que ser posterior al inicio',
    path: ['ends_at'],
  })

type Formulario = z.infer<typeof esquema>

const VACIO: Formulario = { starts_at: '', ends_at: '' }

export default function SlotForm() {
  const queryClient = useQueryClient()
  const { register, handleSubmit, reset, formState } = useForm<Formulario>({
    resolver: zodResolver(esquema),
    defaultValues: VACIO,
  })

  const publicar = useMutation({
    mutationFn: (valores: Formulario) =>
      publishSlot({
        // El backend exige zona horaria. `datetime-local` no la trae, asi que
        // la pone el navegador al pasar a ISO.
        starts_at: new Date(valores.starts_at).toISOString(),
        ends_at: new Date(valores.ends_at).toISOString(),
      }),
    onSuccess: async () => {
      reset(VACIO)
      await queryClient.invalidateQueries({ queryKey: mySlotsQueryKey })
    },
  })

  return (
    <SectionCard
      title="Publicar un tramo"
      description="Un tramo dura entre quince minutos y doce horas, y no puede superponerse con otro tuyo. Dos tramos contiguos sí valen."
    >
      <form
        noValidate
        className="flex flex-col gap-5"
        onSubmit={onSubmit(
          handleSubmit((valores) => {
            publicar.mutate(valores)
          }),
        )}
      >
        <div className="grid gap-5 sm:grid-cols-2">
          <TextField
            id="starts_at"
            label="Desde"
            type="datetime-local"
            field={register('starts_at')}
            error={formState.errors.starts_at?.message}
          />
          <TextField
            id="ends_at"
            label="Hasta"
            type="datetime-local"
            field={register('ends_at')}
            error={formState.errors.ends_at?.message}
          />
        </div>

        {publicar.isError ? (
          <FormMessage tone="error">
            {errorMessage(publicar.error, 'No se pudo publicar el tramo.')}
          </FormMessage>
        ) : null}

        <Button
          type="submit"
          variant="success"
          size="lg"
          className="h-10 self-start px-4"
          disabled={publicar.isPending}
        >
          <Icon name="agregar" size={16} />
          <span>{publicar.isPending ? 'Publicando…' : 'Publicar'}</span>
        </Button>
      </form>
    </SectionCard>
  )
}
