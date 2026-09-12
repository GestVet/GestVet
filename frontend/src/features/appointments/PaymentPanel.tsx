import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { fetchPayments, paymentsQueryKey, voidPayment } from '../../api/payments'
import FormMessage from '../../components/FormMessage'
import { errorMessage } from '../../services/api'
import { useIsStaff } from '../../store/session'
import PaymentForm from './PaymentForm'
import PaymentsTable from './PaymentsTable'

interface PaymentPanelProps {
  readonly appointmentId: number
}

export default function PaymentPanel({ appointmentId }: PaymentPanelProps) {
  const puedeCobrar = useIsStaff()
  const queryClient = useQueryClient()
  const queryKey = paymentsQueryKey({ appointment_id: appointmentId })
  const pagos = useQuery({
    queryKey,
    queryFn: () => fetchPayments({ appointment_id: appointmentId }),
  })

  const anular = useMutation({
    mutationFn: ({ id, motivo }: { id: number; motivo: string }) => voidPayment(id, motivo),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey })
    },
  })

  const pedirAnulacion = (id: number) => {
    const motivo = window.prompt('¿Por qué se anula el pago?')
    if (motivo !== null && motivo.trim() !== '') {
      anular.mutate({ id, motivo })
    }
  }

  if (pagos.isPending) {
    return <p className="empty">Cargando…</p>
  }

  const items = pagos.data?.items ?? []
  const activo = items.find((pago) => !pago.is_voided)

  return (
    <div className="stack">
      {anular.isError ? (
        <FormMessage tone="error">
          {errorMessage(anular.error, 'No se pudo anular el pago.')}
        </FormMessage>
      ) : null}

      {items.length === 0 ? (
        <p className="empty">Todavía no se registró un pago para esta cita.</p>
      ) : (
        <PaymentsTable
          items={items}
          puedeCobrar={puedeCobrar}
          isVoiding={anular.isPending}
          onVoid={pedirAnulacion}
        />
      )}

      {puedeCobrar && activo === undefined ? <PaymentForm appointmentId={appointmentId} /> : null}
    </div>
  )
}
