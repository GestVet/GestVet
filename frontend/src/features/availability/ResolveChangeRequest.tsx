import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { availabilityQueryKey, resolveChangeRequest } from '../../api/availability'
import type { ChangeRequestResponse } from '../../api/types'
import FieldError from '../../components/FieldError'
import FieldIcon from '../../components/FieldIcon'
import FormMessage from '../../components/FormMessage'
import { textoOpcional } from '../../components/formRules'
import Icon from '../../components/Icon'
import { Button } from '../../components/ui/button'
import { Input } from '../../components/ui/input'
import { Label } from '../../components/ui/label'
import { errorMessage } from '../../services/api'

// El mismo tope que el servidor.
const MAX_RESPUESTA = 500

const esquema = z.object({ respuesta: textoOpcional(MAX_RESPUESTA) })

type Formulario = z.infer<typeof esquema>

interface ResolveChangeRequestProps {
  readonly pedido: ChangeRequestResponse
}

export default function ResolveChangeRequest({ pedido }: ResolveChangeRequestProps) {
  const queryClient = useQueryClient()
  const { register, handleSubmit, formState } = useForm<Formulario>({
    resolver: zodResolver(esquema),
    defaultValues: { respuesta: '' },
  })
  const resolver = useMutation({
    mutationFn: (cuerpo: { accepted: boolean; response: string }) =>
      resolveChangeRequest(pedido.id, cuerpo),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: availabilityQueryKey })
    },
  })
  const id = `respuesta-${String(pedido.id)}`
  const errorId = `${id}-error`
  const error = formState.errors.respuesta?.message

  // Aceptar y rechazar validan la misma respuesta y solo difieren en el veredicto.
  const responder = (accepted: boolean) => {
    void handleSubmit((valores) => {
      resolver.mutate({ accepted, response: valores.respuesta })
    })()
  }

  return (
    <div className="flex min-w-56 flex-col gap-2 whitespace-normal">
      <Label htmlFor={id} className="sr-only">
        Respuesta al pedido
      </Label>
      <FieldIcon icon="mensaje">
        <Input
          id={id}
          className="h-8"
          placeholder="Respuesta (opcional)"
          maxLength={MAX_RESPUESTA}
          aria-invalid={error !== undefined}
          aria-describedby={error === undefined ? undefined : errorId}
          {...register('respuesta')}
        />
      </FieldIcon>
      <FieldError id={errorId} message={error} />
      <div className="flex flex-wrap gap-2">
        <Button
          type="button"
          size="sm"
          variant="success"
          disabled={resolver.isPending}
          onClick={() => {
            responder(true)
          }}
        >
          <Icon name="confirmar" size={14} />
          <span>Aceptar</span>
        </Button>
        <Button
          type="button"
          size="sm"
          variant="outline"
          disabled={resolver.isPending}
          onClick={() => {
            responder(false)
          }}
        >
          <Icon name="cancelar" size={14} />
          <span>Rechazar</span>
        </Button>
      </div>
      {resolver.isError ? (
        <FormMessage tone="error">
          {errorMessage(resolver.error, 'No se pudo responder el pedido.')}
        </FormMessage>
      ) : null}
    </div>
  )
}
