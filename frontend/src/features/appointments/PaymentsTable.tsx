import type { PaymentResponse } from '../../api/types'
import DataTable, { type DataColumn } from '../../components/DataTable'
import VoidPaymentDialog from './VoidPaymentDialog'

const FORMATO = new Intl.DateTimeFormat('es-PE', { dateStyle: 'medium', timeStyle: 'short' })

const COLUMNAS: readonly DataColumn<PaymentResponse>[] = [
  { id: 'fecha', header: 'Fecha', cell: (pago) => FORMATO.format(new Date(pago.paid_at)) },
  { id: 'monto', header: 'Monto', cell: (pago) => `S/ ${pago.amount}` },
  { id: 'medio', header: 'Medio', cell: (pago) => pago.method_label },
  { id: 'referencia', header: 'Referencia', cell: (pago) => pago.reference || '—' },
  {
    id: 'estado',
    header: 'Estado',
    className: 'whitespace-normal',
    cell: (pago) =>
      pago.is_voided ? (
        <span className="text-muted-foreground">Anulado: {pago.void_reason}</span>
      ) : (
        'Vigente'
      ),
  },
]

// Anular un pago es cosa del personal: el cliente ve la tabla sin esa columna.
const COLUMNAS_PERSONAL: readonly DataColumn<PaymentResponse>[] = [
  ...COLUMNAS,
  {
    id: 'acciones',
    header: 'Acciones',
    cell: (pago) => (pago.is_voided ? null : <VoidPaymentDialog pago={pago} />),
  },
]

interface PaymentsTableProps {
  readonly items: readonly PaymentResponse[]
  readonly isLoading: boolean
  readonly appointmentId: number
  readonly puedeCobrar: boolean
}

export default function PaymentsTable({ items, isLoading, puedeCobrar }: PaymentsTableProps) {
  return (
    <DataTable
      columns={puedeCobrar ? COLUMNAS_PERSONAL : COLUMNAS}
      data={items}
      isLoading={isLoading}
      emptyMessage="Todavía no se registró un pago para esta cita."
      getRowId={(pago) => String(pago.id)}
    />
  )
}
