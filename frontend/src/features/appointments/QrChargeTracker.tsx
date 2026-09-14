import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { confirmQrCharge, fetchQrCharge, paymentsQueryKey, qrChargeQueryKey } from '../../api/payments'
import { errorMessage } from '../../services/api'
import QrChargeDisplay from './QrChargeDisplay'

const POLL_INTERVAL_MS = 3000

interface QrChargeTrackerProps {
  readonly chargeId: number
  readonly appointmentId: number
  readonly onReset: () => void
}

/** Sigue un cobro por QR ya generado: lo consulta, lo muestra, lo confirma. */
export default function QrChargeTracker({
  chargeId,
  appointmentId,
  onReset,
}: QrChargeTrackerProps) {
  const queryClient = useQueryClient()
  const queryKey = qrChargeQueryKey(chargeId)

  const cobro = useQuery({
    queryKey,
    queryFn: () => fetchQrCharge(chargeId),
    refetchInterval: (query) =>
      query.state.data?.status === 'pending' ? POLL_INTERVAL_MS : false,
    refetchIntervalInBackground: true,
  })

  const confirmar = useMutation({
    mutationFn: () => confirmQrCharge(chargeId),
    onSuccess: async (charge) => {
      queryClient.setQueryData(queryKey, charge)
      await queryClient.invalidateQueries({
        queryKey: paymentsQueryKey({ appointment_id: appointmentId }),
      })
    },
  })

  if (cobro.isPending || cobro.data === undefined) {
    return <p className="m-0 text-sm text-muted-foreground">Generando el código…</p>
  }

  return (
    <QrChargeDisplay
      charge={cobro.data}
      isConfirming={confirmar.isPending}
      confirmError={
        confirmar.isError ? errorMessage(confirmar.error, 'No se pudo confirmar el pago.') : ''
      }
      onConfirm={() => {
        confirmar.mutate()
      }}
      onRetry={onReset}
    />
  )
}
