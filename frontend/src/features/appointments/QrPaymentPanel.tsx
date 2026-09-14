import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation } from '@tanstack/react-query'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { createQrCharge } from '../../api/payments'
import FormMessage from '../../components/FormMessage'
import { decimalParaApi, decimalRule } from '../../components/formRules'
import Icon from '../../components/Icon'
import TextField from '../../components/TextField'
import { Button } from '../../components/ui/button'
import { onSubmit } from '../../hooks/formSubmit'
import { errorMessage } from '../../services/api'
import QrChargeTracker from './QrChargeTracker'

// Vacío es válido: significa cobrar el precio de catálogo.
const esquema = z.object({
  monto: decimalRule({ max: 99999.99, decimales: 2, unidad: 'soles' }),
})

type Formulario = z.infer<typeof esquema>

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
  const { register, handleSubmit, formState } = useForm<Formulario>({
    resolver: zodResolver(esquema),
    defaultValues: { monto: '' },
  })

  const generar = useMutation({
    mutationFn: (valores: Formulario) =>
      createQrCharge(appointmentId, decimalParaApi(valores.monto) ?? ''),
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
    <form
      noValidate
      className="flex flex-col items-start gap-3"
      onSubmit={onSubmit(
        handleSubmit((valores) => {
          generar.mutate(valores)
        }),
      )}
    >
      {generar.isError ? (
        <FormMessage tone="error">
          {errorMessage(generar.error, 'No se pudo generar el QR.')}
        </FormMessage>
      ) : null}
      {puedeAjustarMonto ? (
        <div className="w-full max-w-sm">
          <TextField
            id={`monto-qr-${String(appointmentId)}`}
            label="Monto (opcional)"
            icon="pago"
            inputMode="decimal"
            placeholder="Precio de catálogo"
            hint="Déjalo vacío para usar el precio de catálogo. En una cita normal admite hasta S/ 5 de diferencia; en una emergencia no hay límite."
            field={register('monto')}
            error={formState.errors.monto?.message}
          />
        </div>
      ) : null}
      <Button type="submit" disabled={generar.isPending}>
        <Icon name="pago" size={16} />
        <span>{generar.isPending ? 'Generando…' : 'Pagar con QR'}</span>
      </Button>
    </form>
  )
}
