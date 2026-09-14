import { Separator } from '../../components/ui/separator'
import PaymentForm from './PaymentForm'
import QrPaymentPanel from './QrPaymentPanel'

interface NewPaymentOptionsProps {
  readonly appointmentId: number
  readonly appointmentStatus: string
  readonly puedeCobrar: boolean
}

/** Qué se ofrece para cobrar una cita que todavía no tiene un pago vigente. */
export default function NewPaymentOptions({
  appointmentId,
  appointmentStatus,
  puedeCobrar,
}: NewPaymentOptionsProps) {
  return (
    <div className="flex flex-col gap-4">
      {appointmentStatus === 'completed' ? (
        <QrPaymentPanel appointmentId={appointmentId} puedeAjustarMonto={puedeCobrar} />
      ) : (
        <p className="m-0 text-sm text-muted-foreground">
          El cobro por QR está disponible una vez que la cita se marque como completada.
        </p>
      )}
      {puedeCobrar ? (
        <>
          <Separator />
          <PaymentForm appointmentId={appointmentId} />
        </>
      ) : null}
    </div>
  )
}
