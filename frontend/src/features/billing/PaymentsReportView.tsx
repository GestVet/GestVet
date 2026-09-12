import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'

import {
  fetchPaymentReport,
  fetchPayments,
  paymentReportQueryKey,
  paymentsQueryKey,
} from '../../api/payments'
import TableShell from '../../components/TableShell'
import PaymentReportSummary from './PaymentReportSummary'

const COLUMNAS = ['Fecha', 'Cita', 'Monto', 'Medio', 'Referencia', 'Estado'] as const

const FORMATO = new Intl.DateTimeFormat('es-PE', { dateStyle: 'medium', timeStyle: 'short' })

export default function PaymentsReportView() {
  const [desde, setDesde] = useState('')
  const [hasta, setHasta] = useState('')

  const filtro = {
    starts_after: desde === '' ? undefined : new Date(desde).toISOString(),
    ends_before: hasta === '' ? undefined : new Date(hasta).toISOString(),
  }

  const reporte = useQuery({
    queryKey: paymentReportQueryKey(filtro),
    queryFn: () => fetchPaymentReport(filtro),
  })

  const pagos = useQuery({
    queryKey: paymentsQueryKey(filtro),
    queryFn: () => fetchPayments(filtro),
  })
  const items = pagos.data?.items ?? []

  return (
    <div className="stack">
      <div className="page-header">
        <h1>Pagos</h1>
      </div>

      <section className="card">
        <div className="form" style={{ gridTemplateColumns: 'repeat(2, minmax(0, 1fr))' }}>
          <div className="field">
            <label htmlFor="reporte-desde">Desde</label>
            <input
              id="reporte-desde"
              type="date"
              value={desde}
              onChange={(evento) => {
                setDesde(evento.target.value)
              }}
            />
          </div>
          <div className="field">
            <label htmlFor="reporte-hasta">Hasta</label>
            <input
              id="reporte-hasta"
              type="date"
              value={hasta}
              onChange={(evento) => {
                setHasta(evento.target.value)
              }}
            />
          </div>
        </div>

        <PaymentReportSummary
          isLoading={reporte.isPending}
          items={reporte.data?.items ?? []}
          grandTotal={reporte.data?.grand_total ?? '0'}
        />
      </section>

      <section className="card">
        <TableShell
          columns={COLUMNAS}
          isLoading={pagos.isPending}
          isEmpty={items.length === 0}
          emptyMessage="No hay pagos para mostrar."
        >
          {items.map((pago) => (
            <tr key={pago.id}>
              <td>{FORMATO.format(new Date(pago.paid_at))}</td>
              <td>#{pago.appointment_id}</td>
              <td>S/ {pago.amount}</td>
              <td>{pago.method_label}</td>
              <td>{pago.reference || '—'}</td>
              <td>
                {pago.is_voided ? (
                  <span className="muted">Anulado: {pago.void_reason}</span>
                ) : (
                  'Vigente'
                )}
              </td>
            </tr>
          ))}
        </TableShell>
      </section>
    </div>
  )
}
