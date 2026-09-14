import { useMutation } from '@tanstack/react-query'
import { useState } from 'react'

import { createQrCharge } from '../../api/payments'
import FormMessage from '../../components/FormMessage'
import Icon from '../../components/Icon'
import { Button } from '../../components/ui/button'
import { Input } from '../../components/ui/input'
import { Label } from '../../components/ui/label'
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
  const montoId = `monto-qr-${String(appointmentId)}`

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
    <div className="flex flex-col items-start gap-3">
      {generar.isError ? (
        <FormMessage tone="error">
          {errorMessage(generar.error, 'No se pudo generar el QR.')}
        </FormMessage>
      ) : null}
      {puedeAjustarMonto ? (
        <div className="flex w-full max-w-sm flex-col gap-2">
          <Label htmlFor={montoId}>Monto (opcional)</Label>
          <Input
            id={montoId}
            type="number"
            inputMode="decimal"
            step="0.01"
            min="0"
            className="h-10"
            placeholder="Precio de catálogo"
            aria-describedby={`${montoId}-ayuda`}
            value={monto}
            onChange={(evento) => {
              setMonto(evento.target.value)
            }}
          />
          <p id={`${montoId}-ayuda`} className="m-0 text-sm text-muted-foreground">
            Déjalo vacío para usar el precio de catálogo. En una cita normal admite hasta S/ 5
            de diferencia; en una emergencia no hay límite.
          </p>
        </div>
      ) : null}
      <Button
        type="button"
        disabled={generar.isPending}
        onClick={() => {
          generar.mutate()
        }}
      >
        <Icon name="pago" size={16} />
        <span>{generar.isPending ? 'Generando…' : 'Pagar con QR'}</span>
      </Button>
    </div>
  )
}
