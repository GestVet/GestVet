import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { FormProvider, useForm } from 'react-hook-form'

import { appointmentsQueryKey, bookAppointment } from '../../api/appointments'
import FormMessage from '../../components/FormMessage'
import Icon from '../../components/Icon'
import SectionCard from '../../components/SectionCard'
import { Button } from '../../components/ui/button'
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
    <SectionCard title="Cita con hora">
      <FormProvider {...formulario}>
        <form
          noValidate
          className="flex flex-col gap-5"
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

          <Button
            type="submit"
            variant="success"
            size="lg"
            className="h-10 self-start px-4"
            disabled={reservar.isPending}
          >
            <Icon name="agenda" size={16} />
            <span>{reservar.isPending ? 'Reservando…' : 'Reservar'}</span>
          </Button>
        </form>
      </FormProvider>
    </SectionCard>
  )
}
