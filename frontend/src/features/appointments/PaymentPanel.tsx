import { useQuery } from '@tanstack/react-query'

import { fetchPayments, paymentsQueryKey } from '../../api/payments'
import { useIsStaff } from '../../store/session'
import NewPaymentOptions from './NewPaymentOptions'
import PaymentsTable from './PaymentsTable'

interface PaymentPanelProps {
  readonly appointmentId: number
  readonly appointmentStatus: string
}

export default function PaymentPanel({ appointmentId, appointmentStatus }: PaymentPanelProps) {
  const puedeCobrar = useIsStaff()
  const pagos = useQuery({
    queryKey: paymentsQueryKey({ appointment_id: appointmentId }),
    queryFn: () => fetchPayments({ appointment_id: appointmentId }),
  })

  const items = pagos.data?.items ?? []
  const activo = items.find((pago) => !pago.is_voided)

  return (
    <div className="flex flex-col gap-4">
      <PaymentsTable
        items={items}
        isLoading={pagos.isPending}
        appointmentId={appointmentId}
        puedeCobrar={puedeCobrar}
      />

      {!pagos.isPending && activo === undefined ? (
        <NewPaymentOptions
          appointmentId={appointmentId}
          appointmentStatus={appointmentStatus}
          puedeCobrar={puedeCobrar}
        />
      ) : null}
    </div>
  )
}
