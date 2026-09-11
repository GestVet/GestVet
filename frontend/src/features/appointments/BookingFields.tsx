import { useQuery } from '@tanstack/react-query'
import { useFormContext } from 'react-hook-form'

import { appointmentTypesQueryKey, fetchAppointmentTypes } from '../../api/appointments'
import { fetchVeterinarians, veterinariansQueryKey } from '../../api/directory'
import { fetchMyPets, myPetsQueryKey } from '../../api/pets'
import SelectField from '../../components/SelectField'
import TextField from '../../components/TextField'
import type { BookingForm } from './bookingSchema'

/**
 * Los campos de la reserva.
 *
 * Toma el formulario del contexto en vez de recibirlo por props: asi el
 * formulario que lo envuelve se queda solo con la mutacion y el envio, y
 * ninguno de los dos pasa del limite de tamano.
 */
export default function BookingFields() {
  const { register, formState } = useFormContext<BookingForm>()
  const errores = formState.errors

  const mascotas = useQuery({ queryKey: myPetsQueryKey, queryFn: fetchMyPets })
  const motivos = useQuery({ queryKey: appointmentTypesQueryKey, queryFn: fetchAppointmentTypes })
  const veterinarios = useQuery({ queryKey: veterinariansQueryKey, queryFn: fetchVeterinarians })

  const activas = mascotas.data?.items.filter((mascota) => mascota.is_active) ?? []

  return (
    <>
      <SelectField
        id="pet_id"
        label="Mascota"
        placeholder="Elegí una"
        field={register('pet_id')}
        error={errores.pet_id?.message}
      >
        {activas.map((mascota) => (
          <option key={mascota.id} value={mascota.id}>
            {mascota.name} · {mascota.species}
          </option>
        ))}
      </SelectField>

      <SelectField
        id="veterinarian_id"
        label="Veterinario"
        placeholder="Elegí uno"
        field={register('veterinarian_id')}
        error={errores.veterinarian_id?.message}
      >
        {veterinarios.data?.items.map((veterinario) => (
          <option key={veterinario.id} value={veterinario.id}>
            {veterinario.full_name}
          </option>
        ))}
      </SelectField>

      <SelectField
        id="appointment_type_id"
        label="Motivo"
        placeholder="Elegí el motivo"
        field={register('appointment_type_id')}
        error={errores.appointment_type_id?.message}
      >
        {motivos.data?.items.map((motivo) => (
          <option key={motivo.id} value={motivo.id}>
            {motivo.name} · {motivo.duration_minutes} min · S/ {motivo.price}
          </option>
        ))}
      </SelectField>

      <TextField
        id="scheduled_at"
        label="Fecha y hora"
        type="datetime-local"
        field={register('scheduled_at')}
        error={errores.scheduled_at?.message}
        hint="Tiene que caer dentro de un tramo publicado por el veterinario."
      />

      <TextField
        id="description"
        label="Motivo de consulta"
        field={register('description')}
        error={errores.description?.message}
      />
    </>
  )
}
