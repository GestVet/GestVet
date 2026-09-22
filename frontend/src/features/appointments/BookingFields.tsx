import { useQuery } from '@tanstack/react-query'
import { type FieldErrors, useFormContext, useWatch } from 'react-hook-form'

import { appointmentTypesQueryKey, fetchAppointmentTypes } from '../../api/appointments'
import SelectField from '../../components/SelectField'
import TextareaField from '../../components/TextareaField'
import { NativeSelectOption } from '../../components/ui/native-select'
import type { BookingForm } from './bookingSchema'
import BookingSlotPicker from './BookingSlotPicker'
import PetSelectField from './PetSelectField'
import SpecialtySelectField from './SpecialtySelectField'

function mensajeDeError(errores: FieldErrors<BookingForm>, campo: keyof BookingForm) {
  return errores[campo]?.message
}

/**
 * Los campos de la reserva, en el orden en que se decide.
 *
 * Primero la mascota y el tipo de atención, porque el tipo define la duración
 * y con ella qué horas caben. Recién ahí aparecen los días y las horas libres.
 *
 * Toma el formulario del contexto en vez de recibirlo por props: asi el
 * formulario que lo envuelve se queda solo con la mutacion y el envio.
 */
export default function BookingFields() {
  const { register, control, formState, setValue } = useFormContext<BookingForm>()
  const errores = formState.errors

  const motivos = useQuery({ queryKey: appointmentTypesQueryKey, queryFn: fetchAppointmentTypes })
  const tipoId = Number(useWatch({ control, name: 'appointment_type_id' }) || 0)
  const especialidadId = Number(useWatch({ control, name: 'specialty_id' }) || 0)
  const duracion = motivos.data?.items.find((motivo) => motivo.id === tipoId)?.duration_minutes ?? 0

  const limpiarHora = () => {
    setValue('veterinarian_id', '')
    setValue('scheduled_at', '')
  }

  return (
    <>
      <p className="m-0 text-sm font-semibold">1. ¿Para quién y qué necesita?</p>
      <div className="grid items-start gap-5 sm:grid-cols-2">
        <PetSelectField register={register} error={mensajeDeError(errores, 'pet_id')} />

        <SelectField
          id="appointment_type_id"
          label="Tipo de atención"
          icon="diagnostico"
          placeholder="Elige uno"
          field={register('appointment_type_id', {
            // Otro tipo cambia la duracion: la hora elegida puede dejar de caber.
            onChange: limpiarHora,
          })}
          error={mensajeDeError(errores, 'appointment_type_id')}
          hint="El precio es estimado: puede variar según lo que requiera la atención."
        >
          {motivos.data?.items.map((motivo) => (
            <NativeSelectOption key={motivo.id} value={motivo.id}>
              {motivo.name} · {motivo.duration_minutes} min · S/ {motivo.price}
            </NativeSelectOption>
          ))}
        </SelectField>

        <SpecialtySelectField register={register} onChange={limpiarHora} />
      </div>

      {tipoId > 0 ? (
        // La clave vuelve a montar el selector con cada tipo: el dia elegido
        // para una consulta no tiene por que servir para una cirugia.
        <BookingSlotPicker
          key={tipoId}
          appointmentTypeId={tipoId}
          durationMinutes={duracion}
          specialtyId={especialidadId > 0 ? especialidadId : null}
        />
      ) : (
        <p className="m-0 rounded-lg bg-muted px-4 py-3 text-sm text-muted-foreground">
          Elige el tipo de atención para ver los días y las horas libres.
        </p>
      )}

      <TextareaField
        id="description"
        label="3. ¿Qué le pasa a tu mascota? (opcional)"
        placeholder="Vomita desde ayer y no quiere comer"
        icon="mensaje"
        hint="Ayuda al veterinario a preparar la consulta."
        rows={3}
        field={register('description')}
        error={mensajeDeError(errores, 'description')}
      />
    </>
  )
}
