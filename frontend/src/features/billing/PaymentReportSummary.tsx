import type { MethodTotalResponse } from '../../api/types'

interface PaymentReportSummaryProps {
  readonly isLoading: boolean
  readonly items: readonly MethodTotalResponse[]
  readonly grandTotal: string
}

export default function PaymentReportSummary({
  isLoading,
  items,
  grandTotal,
}: PaymentReportSummaryProps) {
  if (isLoading) {
    return <p className="empty">Cargando…</p>
  }
  if (items.length === 0) {
    return <p className="empty">No hay pagos en el rango elegido.</p>
  }

  return (
    <div className="card-grid">
      {items.map((item) => (
        <div className="tile" key={item.method}>
          <h3>{item.method_label}</h3>
          <p>
            S/ {item.total} · {item.count} {item.count === 1 ? 'pago' : 'pagos'}
          </p>
        </div>
      ))}
      <div className="tile">
        <h3>Total</h3>
        <p>S/ {grandTotal}</p>
      </div>
    </div>
  )
}
