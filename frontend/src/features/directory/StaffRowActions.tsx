import { useMutation, useQueryClient } from '@tanstack/react-query'

import {
  changeUserStatus,
  staffQueryKey,
  toggleEmergencyCoverage,
  toggleGuardDuty,
} from '../../api/directory'
import type { UserResponse } from '../../api/types'
import FormMessage from '../../components/FormMessage'
import Icon from '../../components/Icon'
import { Button } from '../../components/ui/button'
import { errorMessage } from '../../services/api'

function primerError(errores: readonly (Error | null)[]): Error | null {
  return errores.find((error) => error !== null) ?? null
}

interface StaffRowActionsProps {
  readonly account: UserResponse
}

export default function StaffRowActions({ account }: StaffRowActionsProps) {
  const queryClient = useQueryClient()

  const refrescar = async () => {
    await queryClient.invalidateQueries({ queryKey: staffQueryKey })
  }

  const guardia = useMutation({ mutationFn: toggleGuardDuty, onSuccess: refrescar })
  const estado = useMutation({
    mutationFn: () => changeUserStatus(account.id, !account.is_active),
    onSuccess: refrescar,
  })
  const respaldo = useMutation({
    mutationFn: () => toggleEmergencyCoverage(account.id, !account.can_cover_emergencies),
    onSuccess: refrescar,
  })

  const ocupado = guardia.isPending || estado.isPending || respaldo.isPending
  const fallo = primerError([guardia.error, estado.error, respaldo.error])
  const deGuardia = account.role === 'emergency_veterinarian'

  return (
    <div className="flex max-w-md flex-col items-start gap-2 whitespace-normal">
      <div className="flex flex-wrap gap-2">
        <Button
          type="button"
          size="sm"
          disabled={ocupado}
          onClick={() => {
            guardia.mutate(account.id)
          }}
        >
          <Icon name="emergencia" size={14} />
          <span>{deGuardia ? 'Sacar de guardia' : 'Poner de guardia'}</span>
        </Button>

        {deGuardia ? null : (
          <Button
            type="button"
            size="sm"
            variant="outline"
            disabled={ocupado}
            title="Cubre una emergencia si todos los de guardia ya están ocupados y no tiene citas para el resto del día."
            onClick={() => {
              respaldo.mutate()
            }}
          >
            <Icon name="alerta" size={14} />
            <span>
              {account.can_cover_emergencies ? 'Quitar respaldo' : 'Habilitar como respaldo'}
            </span>
          </Button>
        )}

        <Button
          type="button"
          size="sm"
          variant={account.is_active ? 'ghost' : 'success'}
          disabled={ocupado}
          onClick={() => {
            estado.mutate()
          }}
        >
          {account.is_active ? 'Desactivar' : 'Activar'}
        </Button>
      </div>
      {fallo === null ? null : (
        <FormMessage tone="error">{errorMessage(fallo, 'No se pudo actualizar la cuenta.')}</FormMessage>
      )}
    </div>
  )
}
