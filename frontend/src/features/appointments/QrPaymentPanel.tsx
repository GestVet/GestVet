import { useMutation } from '@tanstack/react-query'
import { useState } from 'react'

import { createQrCharge } from '../../api/payments'
import FormMessage from '../../components/FormMessage'
import Icon from '../../components/Icon'
import { errorMessage } from '../../services/api'
import QrChargeTracker from './QrChargeTracker'

interface QrPaymentPanelProps {
  readonly appointmentId: number
  readonly puedeAjustarMonto: boolean
}

/**
 * Cobro por QR de una cita.
 *
 * Lo ve tanto el cliente (autoservicio, siempre al precio de catálogo) como
 * el personal (en el mostrador, que además puede ajustar el monto): el
 * panel de pagos que lo aloja ya solo se muestra sobre citas propias o, si
 * es personal, sobre cualquiera.
 */
export default function QrPaymentPanel({
  appointmentId,
  puedeAjustarMonto,
}: QrPaymentPanelProps) {
  const [chargeId, setChargeId] = useState<number | null>(null)
  const [monto, setMonto] = useState('')

  const generar = useMutation({
    mutationFn: () => createQrCharge(appointmentId, monto),
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
      {puedeAjustarMonto ? (
        <div className="field">
          <label htmlFor="monto-qr">Monto (opcional)</label>
          <input
            id="monto-qr"
            type="number"
            step="0.01"
            min="0"
            placeholder="Dejalo vacío para usar el precio de catálogo"
            value={monto}
            onChange={(evento) => {
              setMonto(evento.target.value)
            }}
          />
          <span className="muted">
            En una cita normal, el monto admite hasta S/ 5 de diferencia con el precio de
            catálogo; en una emergencia no hay límite.
          </span>
        </div>
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
