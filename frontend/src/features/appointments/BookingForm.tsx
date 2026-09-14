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

const VACIO: Valores = {
  pet_id: '',
  appointment_type_id: '',
  veterinarian_id: '',
  scheduled_at: '',
  description: '',
}

export default function BookingForm() {
  const queryClient = useQueryClient()
  const formulario = useForm<Valores>({
    resolver: zodResolver(bookingSchema),
    defaultValues: VACIO,
  })

  const reservar = useMutation({
    mutationFn: (valores: Valores) =>
      bookAppointment({
        pet_id: Number(valores.pet_id),
        veterinarian_id: Number(valores.veterinarian_id),
        appointment_type_id: Number(valores.appointment_type_id),
        // La hora llega del selector tal como la calculo el servidor, en ISO
        // y con zona horaria.
        scheduled_at: valores.scheduled_at,
        description: valores.description,
      }),
    onSuccess: async () => {
      formulario.reset(VACIO)
      // Incluye las horas libres: la que se acaba de tomar deja de ofrecerse.
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
            <FormMessage tone="ok">
              Cita reservada. Queda pendiente de que el veterinario la confirme.
            </FormMessage>
          ) : null}

          <Button
            type="submit"
            variant="success"
            size="lg"
            className="h-11 self-start px-5"
            disabled={reservar.isPending}
          >
            <Icon name="agenda" size={18} />
            <span>{reservar.isPending ? 'Reservando…' : 'Reservar cita'}</span>
          </Button>
        </form>
      </FormProvider>
    </SectionCard>
  )
}
