import { useMutation, useQueryClient } from '@tanstack/react-query'

import { changeUserStatus, staffQueryKey, toggleGuardDuty } from '../../api/directory'
import type { UserResponse } from '../../api/types'
import Icon from '../../components/Icon'

interface StaffRowActionsProps {
  readonly account: UserResponse
  readonly onError: (error: unknown) => void
}

/** Los dos botones de una fila del equipo: turno de guardia y activación. */
export default function StaffRowActions({ account, onError }: StaffRowActionsProps) {
  const queryClient = useQueryClient()

  const refrescar = async () => {
    await queryClient.invalidateQueries({ queryKey: staffQueryKey })
  }

  const guardia = useMutation({
    mutationFn: toggleGuardDuty,
    onSuccess: refrescar,
    onError,
  })
  const estado = useMutation({
    mutationFn: ({ id, activo }: { id: number; activo: boolean }) => changeUserStatus(id, activo),
    onSuccess: refrescar,
    onError,
  })

  const ocupado = guardia.isPending || estado.isPending
  const deGuardia = account.role === 'emergency_veterinarian'

  return (
    <div className="row-actions">
      <button
        type="button"
        className="btn btn-blue"
        disabled={ocupado}
        onClick={() => {
          guardia.mutate(account.id)
        }}
      >
        <Icon name="emergencia" size={14} />
        <span>{deGuardia ? 'Sacar de guardia' : 'Poner de guardia'}</span>
      </button>

      <button
        type="button"
        className={account.is_active ? 'btn btn-plain' : 'btn btn-green'}
        disabled={ocupado}
        onClick={() => {
          estado.mutate({ id: account.id, activo: !account.is_active })
        }}
      >
        {account.is_active ? 'Desactivar' : 'Activar'}
      </button>
    </div>
  )
}
