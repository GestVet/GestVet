import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { paymentsQueryKey, registerPayment } from '../../api/payments'
import FormMessage from '../../components/FormMessage'
import { decimalParaApi, decimalRule, textoOpcional } from '../../components/formRules'
import Icon from '../../components/Icon'
import SectionHeading from '../../components/SectionHeading'
import SelectField from '../../components/SelectField'
import TextField from '../../components/TextField'
import { Button } from '../../components/ui/button'
import { NativeSelectOption } from '../../components/ui/native-select'
import { onSubmit } from '../../hooks/formSubmit'
import { errorMessage } from '../../services/api'

const METODOS = [
  { value: 'cash', label: 'Efectivo' },
  { value: 'yape', label: 'Yape' },
  { value: 'bank_transfer', label: 'Transferencia bancaria' },
  { value: 'other', label: 'Otro' },
] as const

const esquema = z.object({
  amount: decimalRule({ max: 99999.99, decimales: 2, unidad: 'soles', obligatorio: true }),
  method: z.enum(['cash', 'yape', 'bank_transfer', 'other']),
  reference: textoOpcional(120),
})

type Formulario = z.infer<typeof esquema>

const VACIO: Formulario = { amount: '', method: 'cash', reference: '' }

interface PaymentFormProps {
  readonly appointmentId: number
}

export default function PaymentForm({ appointmentId }: PaymentFormProps) {
  const queryClient = useQueryClient()
  const queryKey = paymentsQueryKey({ appointment_id: appointmentId })
  const { register, handleSubmit, reset, formState } = useForm<Formulario>({
    resolver: zodResolver(esquema),
    defaultValues: VACIO,
  })
  const campo = (nombre: string) => `${nombre}-${String(appointmentId)}`

  const registrar = useMutation({
    mutationFn: (valores: Formulario) =>
      registerPayment({
        appointment_id: appointmentId,
        amount: decimalParaApi(valores.amount) ?? '0',
        method: valores.method,
        reference: valores.reference,
        notes: '',
      }),
    onSuccess: async () => {
      reset(VACIO)
      await queryClient.invalidateQueries({ queryKey })
    },
  })

  return (
    <form
      noValidate
      className="flex flex-col gap-4"
      onSubmit={onSubmit(
        handleSubmit((valores) => {
          registrar.mutate(valores)
        }),
      )}
    >
      <SectionHeading as="h3">Registrar un pago en mostrador</SectionHeading>
      <div className="grid gap-5 sm:grid-cols-3">
        <TextField
          id={campo('amount')}
          label="Monto (S/)"
          placeholder="0.00"
          icon="pago"
          type="number"
          inputMode="decimal"
          step="0.01"
          min="0"
          field={register('amount')}
          error={formState.errors.amount?.message}
        />
        <SelectField id={campo('method')} label="Medio de pago" icon="medioDePago" field={register('method')}>
          {METODOS.map((metodo) => (
            <NativeSelectOption key={metodo.value} value={metodo.value}>
              {metodo.label}
            </NativeSelectOption>
          ))}
        </SelectField>
        <TextField
          id={campo('reference')}
          label="Referencia (opcional)"
          icon="numero"
          placeholder="N° de operación"
          maxLength={120}
          field={register('reference')}
          error={formState.errors.reference?.message}
        />
      </div>

      {registrar.isError ? (
        <FormMessage tone="error">
          {errorMessage(registrar.error, 'No se pudo registrar el pago.')}
        </FormMessage>
      ) : null}

      <Button type="submit" variant="success" className="self-start" disabled={registrar.isPending}>
        <Icon name="agregar" size={16} />
        <span>{registrar.isPending ? 'Guardando…' : 'Registrar pago'}</span>
      </Button>
    </form>
  )
}
