import type { MethodTotalResponse } from '../../api/types'
import EmptyState from '../../components/EmptyState'

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
    return <EmptyState title="Cargando…" />
  }
  if (items.length === 0) {
    return <EmptyState title="No hay pagos en el rango elegido." />
  }

  return (
    <dl className="m-0 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      {items.map((item) => (
        <div key={item.method} className="flex flex-col gap-1 rounded-xl bg-muted p-4">
          <dt className="text-sm text-muted-foreground">{item.method_label}</dt>
          <dd className="m-0 font-heading text-xl font-semibold">S/ {item.total}</dd>
          <dd className="m-0 text-sm text-muted-foreground">
            {item.count} {item.count === 1 ? 'pago' : 'pagos'}
          </dd>
        </div>
      ))}
      <div className="flex flex-col gap-1 rounded-xl bg-primary p-4 text-primary-foreground">
        <dt className="text-sm">Total</dt>
        <dd className="m-0 font-heading text-xl font-semibold">S/ {grandTotal}</dd>
      </div>
    </dl>
  )
}
