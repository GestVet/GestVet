import { useMutation, useQueryClient } from '@tanstack/react-query'

import {
  changeUserStatus,
  staffQueryKey,
  toggleEmergencyCoverage,
  toggleGuardDuty,
} from '../../api/directory'
import type { UserResponse } from '../../api/types'
import Icon from '../../components/Icon'

interface StaffRowActionsProps {
  readonly account: UserResponse
  readonly onError: (error: unknown) => void
}

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
  const respaldo = useMutation({
    mutationFn: ({ id, habilitar }: { id: number; habilitar: boolean }) =>
      toggleEmergencyCoverage(id, habilitar),
    onSuccess: refrescar,
    onError,
  })

  const ocupado = guardia.isPending || estado.isPending || respaldo.isPending
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

      {deGuardia ? null : (
        <button
          type="button"
          className="btn btn-plain"
          disabled={ocupado}
          title="Cubre una emergencia si todos los de guardia ya están ocupados y no tiene citas para el resto del día."
          onClick={() => {
            respaldo.mutate({ id: account.id, habilitar: !account.can_cover_emergencies })
          }}
        >
          <Icon name="alerta" size={14} />
          <span>
            {account.can_cover_emergencies ? 'Quitar respaldo' : 'Habilitar como respaldo'}
          </span>
        </button>
      )}

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
