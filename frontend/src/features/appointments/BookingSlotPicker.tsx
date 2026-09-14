import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { useFormContext, useWatch } from 'react-hook-form'

import { fetchOpenTimes, openTimesQueryKey } from '../../api/appointments'
import { fetchVeterinarians, veterinariansQueryKey } from '../../api/directory'
import type { DayOpenTimesResponse, VeterinarianResponse } from '../../api/types'
import FieldError from '../../components/FieldError'
import type { BookingForm } from './bookingSchema'
import {
  DIAS_A_MOSTRAR,
  diasDesdeHoy,
  formatearDiaDeInstante,
  formatearHora,
} from '../../services/clinicTime'
import DayStrip, { type DiaDeReserva } from './DayStrip'
import VeterinarianTimes, { type OfertaDeVeterinario } from './VeterinarianTimes'

interface BookingSlotPickerProps {
  readonly appointmentTypeId: number
}

function ofertasDelDia(
  dia: DayOpenTimesResponse | undefined,
  veterinarios: readonly VeterinarianResponse[],
): OfertaDeVeterinario[] {
  return (dia?.veterinarians ?? []).map((oferta) => {
    const perfil = veterinarios.find((veterinario) => veterinario.id === oferta.veterinarian_id)
    return {
      veterinarianId: oferta.veterinarian_id,
      nombre: perfil?.full_name ?? 'Veterinario',
      calificacion: perfil?.average_rating ?? null,
      times: oferta.times,
    }
  })
}

function diaDeReserva(key: string, conHoras: readonly DayOpenTimesResponse[]): DiaDeReserva {
  const ofertas = conHoras.find((item) => item.day === key)?.veterinarians ?? []
  const horas = ofertas.reduce((total, oferta) => total + oferta.times.length, 0)
  return { key, disponible: horas > 0, horas }
}

/**
 * La eleccion en una frase, o vacio si todavia no hay hora elegida.
 *
 * La region de estado queda siempre montada y solo cambia su texto: asi el
 * lector de pantalla anuncia la eleccion al hacerla.
 */
function textoDeEleccion(scheduledAt: string, elegido: OfertaDeVeterinario | undefined): string {
  if (!scheduledAt || elegido === undefined) {
    return ''
  }
  return `Elegiste el ${formatearDiaDeInstante(scheduledAt)} a las ${formatearHora(scheduledAt)} con ${elegido.nombre}.`
}

/**
 * Elegir dia y hora entre las que de verdad estan libres.
 *
 * Reemplaza al campo de fecha libre, que aceptaba cualquier valor y dejaba que
 * el error llegara recien al enviar. Las horas vienen calculadas por el
 * servidor con las reglas de la reserva, y se actualizan solas si otra persona
 * toma una mientras esta pantalla esta abierta.
 */
export default function BookingSlotPicker({ appointmentTypeId }: BookingSlotPickerProps) {
  const { control, setValue, formState } = useFormContext<BookingForm>()
  const [veterinarianId, scheduledAt] = useWatch({
    control,
    name: ['veterinarian_id', 'scheduled_at'],
  })
  const [diaElegido, setDiaElegido] = useState<string | null>(null)
  const dias = diasDesdeHoy(DIAS_A_MOSTRAR)

  const horas = useQuery({
    queryKey: openTimesQueryKey(appointmentTypeId, dias[0], DIAS_A_MOSTRAR),
    queryFn: () => fetchOpenTimes(appointmentTypeId, dias[0], DIAS_A_MOSTRAR),
  })
  const veterinarios = useQuery({ queryKey: veterinariansQueryKey, queryFn: fetchVeterinarians })

  if (horas.isPending) {
    return <p className="m-0 text-sm text-muted-foreground">Buscando horas libres…</p>
  }
  const conHoras = horas.data?.days ?? []
  if (conHoras.length === 0) {
    return (
      <p className="m-0 rounded-lg bg-muted px-4 py-3 text-sm text-muted-foreground">
        No hay horas libres en las próximas dos semanas para este tipo de atención. Prueba con otro,
        o abre una emergencia si no puede esperar.
      </p>
    )
  }

  const dia = diaElegido ?? conHoras[0].day
  const ofertas = ofertasDelDia(
    conHoras.find((item) => item.day === dia),
    veterinarios.data?.items ?? [],
  )
  const elegido = ofertas.find((oferta) => oferta.veterinarianId === Number(veterinarianId))

  return (
    <fieldset className="m-0 flex min-w-0 flex-col gap-4 border-0 p-0">
      <legend className="mb-2 text-sm font-semibold">2. Elige el día y la hora</legend>
      <DayStrip
        dias={dias.map((key) => diaDeReserva(key, conHoras))}
        seleccionado={dia}
        onSelect={(key) => {
          setDiaElegido(key)
          setValue('veterinarian_id', '')
          setValue('scheduled_at', '')
        }}
      />
      <VeterinarianTimes
        ofertas={ofertas}
        veterinarianId={Number(veterinarianId)}
        scheduledAt={scheduledAt}
        onSelect={(vet, time) => {
          setValue('veterinarian_id', String(vet), { shouldValidate: true })
          setValue('scheduled_at', time, { shouldValidate: true })
        }}
      />
      <p role="status" className="m-0 empty:hidden rounded-lg bg-secondary px-4 py-3 text-sm text-secondary-foreground">
        {textoDeEleccion(scheduledAt, elegido)}
      </p>
      <FieldError id="scheduled_at-error" message={formState.errors.scheduled_at?.message} />
    </fieldset>
  )
}
