import { useMutation, useQueryClient } from '@tanstack/react-query'

import { changeUserStatus, clientsQueryKey } from '../../api/directory'
import FormMessage from '../../components/FormMessage'
import { Button } from '../../components/ui/button'
import { errorMessage } from '../../services/api'

interface ClientStatusToggleProps {
  readonly clientId: number
  readonly isActive: boolean
}

export default function ClientStatusToggle({ clientId, isActive }: ClientStatusToggleProps) {
  const queryClient = useQueryClient()
  const estado = useMutation({
    mutationFn: () => changeUserStatus(clientId, !isActive),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: clientsQueryKey })
    },
  })

  return (
    <div className="flex flex-col items-start gap-2 whitespace-normal">
      <Button
        type="button"
        size="sm"
        variant={isActive ? 'outline' : 'success'}
        disabled={estado.isPending}
        onClick={() => {
          estado.mutate()
        }}
      >
        {isActive ? 'Desactivar' : 'Activar'}
      </Button>
      {estado.isError ? (
        <FormMessage tone="error">
          {errorMessage(estado.error, 'No se pudo actualizar la cuenta.')}
        </FormMessage>
      ) : null}
    </div>
  )
}
