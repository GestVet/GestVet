import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { clientsQueryKey, updateClientContact } from '../../api/directory'
import FormMessage from '../../components/FormMessage'
import TextField from '../../components/TextField'
import { Button } from '../../components/ui/button'
import { onSubmit } from '../../hooks/formSubmit'
import { errorMessage } from '../../services/api'

const esquema = z.object({
  email: z.email('Ingresá un correo válido'),
  phone: z.string().max(32).optional(),
})

type Formulario = z.infer<typeof esquema>

interface CompleteContactFormProps {
  readonly clientId: number
  readonly phone: string
}

/** Completa el correo real de un cliente dado de alta por emergencia. */
export default function CompleteContactForm({ clientId, phone }: CompleteContactFormProps) {
  const queryClient = useQueryClient()
  const { register, handleSubmit, formState } = useForm<Formulario>({
    resolver: zodResolver(esquema),
    defaultValues: { email: '', phone },
  })

  const completar = useMutation({
    mutationFn: (valores: Formulario) =>
      updateClientContact(clientId, {
        email: valores.email,
        phone: valores.phone ?? '',
        document_id: '',
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: clientsQueryKey })
    },
  })

  if (completar.isSuccess) {
    return <FormMessage tone="ok">Contacto completado. Ya puede entrar con ese correo.</FormMessage>
  }

  return (
    <form
      noValidate
      className="flex flex-col gap-5"
      onSubmit={onSubmit(
        handleSubmit((valores) => {
          completar.mutate(valores)
        }),
      )}
    >
      <div className="grid gap-5 sm:grid-cols-2">
        <TextField
          id={`contacto-correo-${String(clientId)}`}
          label="Correo real del cliente"
          type="email"
          field={register('email')}
          error={formState.errors.email?.message}
        />
        <TextField
          id={`contacto-telefono-${String(clientId)}`}
          label="Teléfono"
          type="tel"
          inputMode="tel"
          field={register('phone')}
        />
      </div>

      {completar.isError ? (
        <FormMessage tone="error">
          {errorMessage(completar.error, 'No se pudo completar el contacto.')}
        </FormMessage>
      ) : null}

      <Button type="submit" className="self-start" disabled={completar.isPending}>
        {completar.isPending ? 'Guardando…' : 'Guardar contacto'}
      </Button>
    </form>
  )
}
