import { useMutation, useQueryClient } from '@tanstack/react-query'

import { changeUserStatus, staffQueryKey } from '../../api/directory'
import type { UserResponse } from '../../api/types'
import FormMessage from '../../components/FormMessage'
import { Button } from '../../components/ui/button'
import { errorMessage } from '../../services/api'

interface StaffRowActionsProps {
  readonly account: UserResponse
}

/**
 * Lo que se hace con una cuenta del personal desde el listado.
 *
 * La guardia ya no se da desde acá: es un turno más, y se asigna en
 * Turnos y guardias.
 */
export default function StaffRowActions({ account }: StaffRowActionsProps) {
  const queryClient = useQueryClient()
  const estado = useMutation({
    mutationFn: () => changeUserStatus(account.id, !account.is_active),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: staffQueryKey })
    },
  })

  return (
    <div className="flex max-w-md flex-col items-start gap-2 whitespace-normal">
      <Button
        type="button"
        size="sm"
        variant={account.is_active ? 'ghost' : 'success'}
        disabled={estado.isPending}
        onClick={() => {
          estado.mutate()
        }}
      >
        {account.is_active ? 'Desactivar' : 'Activar'}
      </Button>
      {estado.isError ? (
        <FormMessage tone="error">
          {errorMessage(estado.error, 'No se pudo actualizar la cuenta.')}
        </FormMessage>
      ) : null}
    </div>
  )
}
