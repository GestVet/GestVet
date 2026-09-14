import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'

import { availabilityQueryKey, resolveChangeRequest } from '../../api/availability'
import type { ChangeRequestResponse } from '../../api/types'
import FormMessage from '../../components/FormMessage'
import Icon from '../../components/Icon'
import { Button } from '../../components/ui/button'
import { Input } from '../../components/ui/input'
import { Label } from '../../components/ui/label'
import { errorMessage } from '../../services/api'

const MAX_RESPUESTA = 500

interface ResolveChangeRequestProps {
  readonly pedido: ChangeRequestResponse
}

export default function ResolveChangeRequest({ pedido }: ResolveChangeRequestProps) {
  const queryClient = useQueryClient()
  const [respuesta, setRespuesta] = useState('')
  const resolver = useMutation({
    mutationFn: (accepted: boolean) =>
      resolveChangeRequest(pedido.id, { accepted, response: respuesta.trim() }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: availabilityQueryKey })
    },
  })
  const id = `respuesta-${String(pedido.id)}`

  return (
    <div className="flex min-w-56 flex-col gap-2 whitespace-normal">
      <Label htmlFor={id} className="sr-only">
        Respuesta al pedido
      </Label>
      <Input
        id={id}
        className="h-8"
        placeholder="Respuesta (opcional)"
        maxLength={MAX_RESPUESTA}
        value={respuesta}
        onChange={(evento) => {
          setRespuesta(evento.target.value)
        }}
      />
      <div className="flex flex-wrap gap-2">
        <Button
          type="button"
          size="sm"
          variant="success"
          disabled={resolver.isPending}
          onClick={() => {
            resolver.mutate(true)
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
            resolver.mutate(false)
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
