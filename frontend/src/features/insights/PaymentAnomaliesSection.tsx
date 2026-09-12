import { useQuery } from '@tanstack/react-query'

import { fetchPaymentAnomalies, paymentAnomaliesQueryKey } from '../../api/insights'
import TableShell from '../../components/TableShell'

const COLUMNAS = ['Pago', 'Cita', 'Tipo', 'Monto', 'Típico', 'Cuándo'] as const
const FORMATO = new Intl.DateTimeFormat('es-PE', { dateStyle: 'medium', timeStyle: 'short' })

export default function PaymentAnomaliesSection() {
  const anomalias = useQuery({
    queryKey: paymentAnomaliesQueryKey,
    queryFn: fetchPaymentAnomalies,
  })
  const items = anomalias.data?.items ?? []

  return (
    <section className="card">
      <h2>Pagos fuera de lo típico</h2>
      <p className="muted">
        Pagos de los últimos 30 días cuyo monto se aleja bastante del promedio de su tipo de cita.
        Las emergencias no entran, porque su precio varía por diseño.
      </p>
      <TableShell
        columns={COLUMNAS}
        isLoading={anomalias.isPending}
        isEmpty={items.length === 0}
        emptyMessage="No hay pagos fuera de lo típico."
      >
        {items.map((item) => (
          <tr key={item.payment_id}>
            <td>#{item.payment_id}</td>
            <td>#{item.appointment_id}</td>
            <td>{item.appointment_type_label}</td>
            <td>S/ {item.amount}</td>
            <td>S/ {item.typical_amount}</td>
            <td>{FORMATO.format(new Date(item.paid_at))}</td>
          </tr>
        ))}
      </TableShell>
    </section>
  )
}
