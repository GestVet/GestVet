import FormMessage from '../../components/FormMessage'
import { Button } from '../../components/ui/button'

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
      <div className="flex flex-col items-start gap-3">
        <FormMessage tone="error">Este QR {charge.status_label.toLowerCase()}.</FormMessage>
        <Button type="button" variant="outline" onClick={onRetry}>
          Generar uno nuevo
        </Button>
      </div>
    )
  }

  return (
    <div className="flex flex-col items-start gap-3">
      <img
        src={charge.qr_image_data_url}
        alt="Código QR para pagar la cita"
        width={200}
        height={200}
        className="rounded-xl bg-white p-2 ring-1 ring-foreground/10"
      />
      <p className="m-0 text-sm text-muted-foreground">
        Escaneá el código con tu app de pagos. Monto: S/ {charge.amount}
      </p>
      {confirmError !== '' ? <FormMessage tone="error">{confirmError}</FormMessage> : null}
      <Button
        type="button"
        variant="outline"
        className="whitespace-normal"
        disabled={isConfirming}
        onClick={onConfirm}
      >
        {isConfirming ? 'Confirmando…' : 'Simular confirmación del banco (modo de prueba)'}
      </Button>
    </div>
  )
}
