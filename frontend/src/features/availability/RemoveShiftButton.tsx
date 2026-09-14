import { useMutation, useQueryClient } from '@tanstack/react-query'

import { availabilityQueryKey, removeShift } from '../../api/availability'
import type { SlotResponse } from '../../api/types'
import ConfirmDialog from '../../components/ConfirmDialog'
import FormMessage from '../../components/FormMessage'
import Icon from '../../components/Icon'
import { Button } from '../../components/ui/button'
import { errorMessage } from '../../services/api'
import { formatearDiaDeInstante } from '../../services/clinicTime'
import { ETIQUETA_DE_TURNO, horarioDeTurno } from './shiftKinds'

interface RemoveShiftButtonProps {
  readonly turno: SlotResponse
  readonly nombre: string
}

export default function RemoveShiftButton({ turno, nombre }: RemoveShiftButtonProps) {
  const queryClient = useQueryClient()
  const quitar = useMutation({
    mutationFn: () => removeShift(turno.id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: availabilityQueryKey })
    },
  })

  return (
    <div className="flex flex-col items-end gap-1">
      <ConfirmDialog
        trigger={
          <Button
            type="button"
            variant="ghost"
            size="icon-sm"
            aria-label={`Quitar el turno de ${nombre}`}
            disabled={quitar.isPending}
          >
            <Icon name="cancelar" size={14} />
          </Button>
        }
        title="¿Quitar este turno?"
        description={`${ETIQUETA_DE_TURNO[turno.kind]} de ${nombre}, ${formatearDiaDeInstante(turno.starts_at)}, ${horarioDeTurno(turno)}. Si tiene citas reservadas no se puede quitar.`}
        confirmLabel="Quitar turno"
        onConfirm={() => {
          quitar.mutate()
        }}
      />
      {quitar.isError ? (
        <FormMessage tone="error">{errorMessage(quitar.error, 'No se pudo quitar el turno.')}</FormMessage>
      ) : null}
    </div>
  )
}
