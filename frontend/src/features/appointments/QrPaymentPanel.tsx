import { useMutation } from '@tanstack/react-query'
import { useState } from 'react'

import { createQrCharge } from '../../api/payments'
import FormMessage from '../../components/FormMessage'
import Icon from '../../components/Icon'
import { errorMessage } from '../../services/api'
import QrChargeTracker from './QrChargeTracker'

interface QrPaymentPanelProps {
  readonly appointmentId: number
}

/**
 * Cobro por QR de una cita.
 *
 * Lo ve tanto el cliente (autoservicio) como el personal (en el mostrador):
 * el panel de pagos que lo aloja ya solo se muestra sobre citas propias o,
 * si es personal, sobre cualquiera.
 */
export default function QrPaymentPanel({ appointmentId }: QrPaymentPanelProps) {
  const [chargeId, setChargeId] = useState<number | null>(null)

  const generar = useMutation({
    mutationFn: () => createQrCharge(appointmentId),
    onSuccess: (charge) => {
      setChargeId(charge.id)
    },
  })

  if (chargeId !== null) {
    return (
      <QrChargeTracker
        chargeId={chargeId}
        appointmentId={appointmentId}
        onReset={() => {
          setChargeId(null)
        }}
      />
    )
  }

  return (
    <div className="stack">
      {generar.isError ? (
        <FormMessage tone="error">
          {errorMessage(generar.error, 'No se pudo generar el QR.')}
        </FormMessage>
      ) : null}
      <button
        type="button"
        className="btn btn-plain"
        disabled={generar.isPending}
        onClick={() => {
          generar.mutate()
        }}
      >
        <Icon name="pago" size={16} />
        <span>{generar.isPending ? 'Generando…' : 'Pagar con QR'}</span>
      </button>
    </div>
  )
}
