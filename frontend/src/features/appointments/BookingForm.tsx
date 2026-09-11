import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { FormProvider, useForm } from 'react-hook-form'

import { appointmentsQueryKey, bookAppointment } from '../../api/appointments'
import FormMessage from '../../components/FormMessage'
import Icon from '../../components/Icon'
import { onSubmit } from '../../hooks/formSubmit'
import { errorMessage } from '../../services/api'
import BookingFields from './BookingFields'
import { bookingSchema, type BookingForm as Valores } from './bookingSchema'

export default function BookingForm() {
  const queryClient = useQueryClient()
  const formulario = useForm<Valores>({
    resolver: zodResolver(bookingSchema),
    defaultValues: {
      pet_id: '',
      veterinarian_id: '',
      appointment_type_id: '',
      scheduled_at: '',
      description: '',
    },
  })

  const reservar = useMutation({
    mutationFn: (valores: Valores) =>
      bookAppointment({
        pet_id: Number(valores.pet_id),
        veterinarian_id: Number(valores.veterinarian_id),
        appointment_type_id: Number(valores.appointment_type_id),
        // El backend exige zona horaria. `datetime-local` no la trae, asi que
        // la pone el navegador al pasar a ISO.
        scheduled_at: new Date(valores.scheduled_at).toISOString(),
        description: valores.description ?? '',
      }),
    onSuccess: async () => {
      formulario.reset()
      await queryClient.invalidateQueries({ queryKey: appointmentsQueryKey })
    },
  })

  return (
    <section className="card">
      <FormProvider {...formulario}>
        <form
          className="form"
          onSubmit={onSubmit(
            formulario.handleSubmit((valores) => {
              reservar.mutate(valores)
            }),
          )}
        >
          <BookingFields />

          {reservar.isError ? (
            <FormMessage tone="error">
              {errorMessage(reservar.error, 'No se pudo reservar la cita.')}
            </FormMessage>
          ) : null}
          {reservar.isSuccess ? (
            <FormMessage tone="ok">Cita reservada. Queda pendiente de confirmar.</FormMessage>
          ) : null}

          <button type="submit" className="btn btn-green" disabled={reservar.isPending}>
            <Icon name="agenda" size={16} />
            <span>{reservar.isPending ? 'Reservando…' : 'Reservar'}</span>
          </button>
        </form>
      </FormProvider>
    </section>
  )
}
