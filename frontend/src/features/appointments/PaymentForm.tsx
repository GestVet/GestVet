import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { paymentsQueryKey, registerPayment } from '../../api/payments'
import FieldError from '../../components/FieldError'
import FormMessage from '../../components/FormMessage'
import Icon from '../../components/Icon'
import SelectField from '../../components/SelectField'
import { onSubmit } from '../../hooks/formSubmit'
import { errorMessage } from '../../services/api'

const METODOS = [
  { value: 'cash', label: 'Efectivo' },
  { value: 'yape', label: 'Yape' },
  { value: 'bank_transfer', label: 'Transferencia bancaria' },
  { value: 'other', label: 'Otro' },
] as const

const esquema = z.object({
  amount: z.string().min(1, 'Ingresá el monto'),
  method: z.enum(['cash', 'yape', 'bank_transfer', 'other']),
  reference: z.string().max(120).optional(),
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

  const registrar = useMutation({
    mutationFn: (valores: Formulario) =>
      registerPayment({
        appointment_id: appointmentId,
        amount: valores.amount,
        method: valores.method,
        reference: valores.reference ?? '',
        notes: '',
      }),
    onSuccess: async () => {
      reset(VACIO)
      await queryClient.invalidateQueries({ queryKey })
    },
  })

  return (
    <form
      className="form"
      onSubmit={onSubmit(
        handleSubmit((valores) => {
          registrar.mutate(valores)
        }),
      )}
    >
      <div className="field">
        <label htmlFor="amount">Monto (S/)</label>
        <input id="amount" type="number" step="0.01" min="0" {...register('amount')} />
        <FieldError message={formState.errors.amount?.message} />
      </div>

      <SelectField id="method" label="Medio de pago" field={register('method')}>
        {METODOS.map((metodo) => (
          <option key={metodo.value} value={metodo.value}>
            {metodo.label}
          </option>
        ))}
      </SelectField>

      <div className="field">
        <label htmlFor="reference">Referencia (opcional)</label>
        <input id="reference" placeholder="N° de operación" {...register('reference')} />
      </div>

      {registrar.isError ? (
        <FormMessage tone="error">
          {errorMessage(registrar.error, 'No se pudo registrar el pago.')}
        </FormMessage>
      ) : null}

      <button type="submit" className="btn btn-green" disabled={registrar.isPending}>
        <Icon name="agregar" size={16} />
        <span>{registrar.isPending ? 'Guardando…' : 'Registrar pago'}</span>
      </button>
    </form>
  )
}
