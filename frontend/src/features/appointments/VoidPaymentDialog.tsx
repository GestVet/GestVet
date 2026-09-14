import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { paymentsQueryKey, voidPayment } from '../../api/payments'
import type { PaymentResponse } from '../../api/types'
import FormMessage from '../../components/FormMessage'
import { MIN_TEXTO, textoObligatorio } from '../../components/formRules'
import TextareaField from '../../components/TextareaField'
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
import { onSubmit } from '../../hooks/formSubmit'
import { errorMessage } from '../../services/api'

// El mismo tope que el servidor.
const MAX_MOTIVO = 300

const esquema = z.object({ motivo: textoObligatorio(MAX_MOTIVO, 'Escribe el motivo') })

type Formulario = z.infer<typeof esquema>

const VACIO: Formulario = { motivo: '' }

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
  const { register, handleSubmit, reset, formState } = useForm<Formulario>({
    resolver: zodResolver(esquema),
    defaultValues: VACIO,
  })

  const anular = useMutation({
    mutationFn: (valores: Formulario) => voidPayment(pago.id, valores.motivo),
    onSuccess: async () => {
      setAbierto(false)
      reset(VACIO)
      await queryClient.invalidateQueries({
        queryKey: paymentsQueryKey({ appointment_id: pago.appointment_id }),
      })
    },
  })

  return (
    <AlertDialog
      open={abierto}
      onOpenChange={(abrir) => {
        setAbierto(abrir)
        reset(VACIO)
      }}
    >
      <AlertDialogTrigger asChild>
        <Button type="button" variant="ghost" size="sm">
          Anular
        </Button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <form
          noValidate
          className="grid gap-4"
          onSubmit={onSubmit(handleSubmit((valores) => { anular.mutate(valores) }))}
        >
          <AlertDialogHeader>
            <AlertDialogTitle>Anular el pago de S/ {pago.amount}</AlertDialogTitle>
            <AlertDialogDescription>
              El pago queda registrado como anulado, con el motivo que escribas.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <TextareaField
            id={`motivo-anulacion-${String(pago.id)}`}
            label="Motivo"
            icon="mensaje"
            rows={2}
            maxLength={MAX_MOTIVO}
            placeholder="Por ejemplo: el pago se registró dos veces"
            hint={`Entre ${String(MIN_TEXTO)} y ${String(MAX_MOTIVO)} caracteres.`}
            field={register('motivo')}
            error={formState.errors.motivo?.message}
          />
          {anular.isError ? (
            <FormMessage tone="error">
              {errorMessage(anular.error, 'No se pudo anular el pago.')}
            </FormMessage>
          ) : null}
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <Button type="submit" variant="danger" disabled={anular.isPending}>
              {anular.isPending ? 'Anulando…' : 'Anular pago'}
            </Button>
          </AlertDialogFooter>
        </form>
      </AlertDialogContent>
    </AlertDialog>
  )
}
