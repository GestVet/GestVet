import type { PaymentResponse } from '../../api/types'

const FORMATO = new Intl.DateTimeFormat('es-PE', { dateStyle: 'medium', timeStyle: 'short' })

interface PaymentsTableProps {
  readonly items: readonly PaymentResponse[]
  readonly puedeCobrar: boolean
  readonly isVoiding: boolean
  readonly onVoid: (id: number) => void
}

export default function PaymentsTable({
  items,
  puedeCobrar,
  isVoiding,
  onVoid,
}: PaymentsTableProps) {
  return (
    <table>
      <thead>
        <tr>
          <th>Fecha</th>
          <th>Monto</th>
          <th>Medio</th>
          <th>Referencia</th>
          <th>Estado</th>
          {puedeCobrar ? <th>Acciones</th> : null}
        </tr>
      </thead>
      <tbody>
        {items.map((pago) => (
          <tr key={pago.id}>
            <td>{FORMATO.format(new Date(pago.paid_at))}</td>
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
            {puedeCobrar && !pago.is_voided ? (
              <td>
                <button
                  type="button"
                  className="btn btn-plain"
                  disabled={isVoiding}
                  onClick={() => {
                    onVoid(pago.id)
                  }}
                >
                  Anular
                </button>
              </td>
            ) : null}
          </tr>
        ))}
      </tbody>
    </table>
  )
}
