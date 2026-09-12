import { useMutation, useQueryClient } from '@tanstack/react-query'

import { mySlotsQueryKey, withdrawSlot } from '../../api/availability'
import FormMessage from '../../components/FormMessage'
import Icon from '../../components/Icon'
import { Button } from '../../components/ui/button'
import { errorMessage } from '../../services/api'

interface WithdrawSlotButtonProps {
  readonly slotId: number
}

export default function WithdrawSlotButton({ slotId }: WithdrawSlotButtonProps) {
  const queryClient = useQueryClient()
  const retirar = useMutation({
    mutationFn: () => withdrawSlot(slotId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: mySlotsQueryKey })
    },
  })

  return (
    <div className="flex flex-col items-start gap-2 whitespace-normal">
      <Button
        type="button"
        variant="outline"
        size="sm"
        disabled={retirar.isPending}
        onClick={() => {
          retirar.mutate()
        }}
      >
        <Icon name="cancelar" size={14} />
        <span>{retirar.isPending ? 'Retirando…' : 'Retirar'}</span>
      </Button>
      {retirar.isError ? (
        <FormMessage tone="error">
          {errorMessage(retirar.error, 'No se pudo retirar el tramo.')}
        </FormMessage>
      ) : null}
    </div>
  )
}
