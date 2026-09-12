import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'

import { paymentsQueryKey, voidPayment } from '../../api/payments'
import type { PaymentResponse } from '../../api/types'
import FormMessage from '../../components/FormMessage'
import {
  AlertDialog,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '../../components/ui/alert-dialog'
import { Button } from '../../components/ui/button'
import { Label } from '../../components/ui/label'
import { Textarea } from '../../components/ui/textarea'
import { errorMessage } from '../../services/api'

interface VoidPaymentDialogProps {
  readonly pago: PaymentResponse
}

/**
 * Anula un pago, con el motivo obligatorio.
 *
 * Reemplaza a `window.prompt`, que no tomaba el tema y no se leía bien con
 * lector de pantalla.
 */
export default function VoidPaymentDialog({ pago }: VoidPaymentDialogProps) {
  const queryClient = useQueryClient()
  const [abierto, setAbierto] = useState(false)
  const [motivo, setMotivo] = useState('')
  const motivoId = `motivo-anulacion-${String(pago.id)}`

  const anular = useMutation({
    mutationFn: () => voidPayment(pago.id, motivo),
    onSuccess: async () => {
      setAbierto(false)
      setMotivo('')
      await queryClient.invalidateQueries({
        queryKey: paymentsQueryKey({ appointment_id: pago.appointment_id }),
      })
    },
  })

  return (
    <AlertDialog open={abierto} onOpenChange={setAbierto}>
      <AlertDialogTrigger asChild>
        <Button type="button" variant="ghost" size="sm">
          Anular
        </Button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Anular el pago de S/ {pago.amount}</AlertDialogTitle>
          <AlertDialogDescription>
            El pago queda registrado como anulado, con el motivo que escribas.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <div className="flex flex-col gap-2">
          <Label htmlFor={motivoId}>Motivo</Label>
          <Textarea
            id={motivoId}
            rows={2}
            value={motivo}
            onChange={(evento) => {
              setMotivo(evento.target.value)
            }}
          />
        </div>
        {anular.isError ? (
          <FormMessage tone="error">
            {errorMessage(anular.error, 'No se pudo anular el pago.')}
          </FormMessage>
        ) : null}
        <AlertDialogFooter>
          <AlertDialogCancel>Cancelar</AlertDialogCancel>
          <Button
            type="button"
            variant="danger"
            disabled={anular.isPending || motivo.trim() === ''}
            onClick={() => {
              anular.mutate()
            }}
          >
            {anular.isPending ? 'Anulando…' : 'Anular pago'}
          </Button>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
