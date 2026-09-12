import FormMessage from '../../components/FormMessage'

interface QrChargeLike {
  readonly status: string
  readonly status_label: string
  readonly qr_image_data_url: string
  readonly amount: string
}

interface QrChargeDisplayProps {
  readonly charge: QrChargeLike
  readonly isConfirming: boolean
  readonly confirmError: string
  readonly onConfirm: () => void
  readonly onRetry: () => void
}

export default function QrChargeDisplay({
  charge,
  isConfirming,
  confirmError,
  onConfirm,
  onRetry,
}: QrChargeDisplayProps) {
  if (charge.status === 'paid') {
    return <FormMessage tone="ok">Pago confirmado por QR.</FormMessage>
  }

  if (charge.status !== 'pending') {
    return (
      <div className="stack">
        <FormMessage tone="error">Este QR {charge.status_label.toLowerCase()}.</FormMessage>
        <button type="button" className="btn btn-plain" onClick={onRetry}>
          Generar uno nuevo
        </button>
      </div>
    )
  }

  return (
    <div className="stack">
      <img
        src={charge.qr_image_data_url}
        alt="Código QR para pagar la cita"
        width={200}
        height={200}
      />
      <p className="muted">Escaneá el código con tu app de pagos. Monto: S/ {charge.amount}</p>
      {confirmError !== '' ? <FormMessage tone="error">{confirmError}</FormMessage> : null}
      <button type="button" className="btn btn-plain" disabled={isConfirming} onClick={onConfirm}>
        {isConfirming ? 'Confirmando…' : 'Simular confirmación del banco (modo de prueba)'}
      </button>
    </div>
  )
}
