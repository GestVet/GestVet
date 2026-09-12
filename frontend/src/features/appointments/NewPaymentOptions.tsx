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
    <>
      {appointmentStatus === 'completed' ? (
        <QrPaymentPanel appointmentId={appointmentId} puedeAjustarMonto={puedeCobrar} />
      ) : (
        <p className="muted">
          El cobro por QR está disponible una vez que la cita se marque como completada.
        </p>
      )}
      {puedeCobrar ? <PaymentForm appointmentId={appointmentId} /> : null}
    </>
  )
}
