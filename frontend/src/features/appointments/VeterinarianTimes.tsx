import type { GridSlotResponse, ScheduleWindowResponse } from '../../api/types'
import { formatearHora24 } from '../../services/clinicTime'
import CustomTimeInput from './CustomTimeInput'
import TimeSlotGroup from './TimeSlotGroup'

export interface OfertaDeVeterinario {
  readonly veterinarianId: number
  readonly nombre: string
  readonly calificacion: string | null
  readonly windows: readonly ScheduleWindowResponse[]
  readonly slots: readonly GridSlotResponse[]
}

interface VeterinarianTimesProps {
  readonly ofertas: readonly OfertaDeVeterinario[]
  /** AAAA-MM-DD del día elegido, en la fecha de la clínica. */
  readonly dia: string
  readonly durationMinutes: number
  readonly veterinarianId: number
  readonly scheduledAt: string
  readonly onSelect: (veterinarianId: number, time: string) => void
}

// Una lista de veinte horas seguidas no se lee: partida en mañana, tarde y
// noche, la persona va directo a la parte del día que le sirve.
const FRANJAS: readonly { readonly nombre: string; readonly desde: number; readonly hasta: number }[] =
  [
    { nombre: 'Mañana', desde: 0, hasta: 12 },
    { nombre: 'Tarde', desde: 12, hasta: 18 },
    { nombre: 'Noche', desde: 18, hasta: 24 },
  ]

function horaDelDia(time: string): number {
  return Number(formatearHora24(time).slice(0, 2))
}

function porFranja(slots: readonly GridSlotResponse[]) {
  return FRANJAS.map((franja) => ({
    nombre: franja.nombre,
    slots: slots.filter(
      (slot) => horaDelDia(slot.time) >= franja.desde && horaDelDia(slot.time) < franja.hasta,
    ),
  })).filter((franja) => franja.slots.length > 0)
}

function iniciales(nombre: string): string {
  return nombre
    .split(' ')
    .filter((parte) => parte !== '')
    .slice(0, 2)
    .map((parte) => parte.charAt(0).toUpperCase())
    .join('')
}

function horariosLibres(slots: readonly GridSlotResponse[]): number {
  return slots.filter((slot) => slot.status === 'available').length
}

// Cuenta horas de inicio posibles, no horas de reloj: con una grilla de 15
// minutos, "29 horas" confundía.
function textoDeDisponibles(cantidad: number): string {
  if (cantidad === 0) {
    return 'Sin horarios disponibles'
  }
  return cantidad === 1 ? '1 horario disponible' : `${String(cantidad)} horarios disponibles`
}

/**
 * Los veterinarios con turno en el dia elegido, cada uno con sus horas.
 *
 * Con un solo veterinario es una lista de horas; con varios, la persona puede
 * elegir por hora o por profesional sin cambiar de pantalla.
 */
export default function VeterinarianTimes({
  ofertas,
  dia,
  durationMinutes,
  veterinarianId,
  scheduledAt,
  onSelect,
}: VeterinarianTimesProps) {
  return (
    <ul className="m-0 grid list-none gap-3 p-0">
      {ofertas.map((oferta) => {
        const libres = horariosLibres(oferta.slots)
        return (
          <li key={oferta.veterinarianId} className="flex flex-col gap-3 rounded-lg border bg-card p-4">
            <div className="flex items-center gap-3">
              <span
                aria-hidden="true"
                className="flex size-9 shrink-0 items-center justify-center rounded-full bg-secondary text-sm font-semibold text-secondary-foreground"
              >
                {iniciales(oferta.nombre)}
              </span>
              <p className="m-0 flex flex-wrap items-baseline gap-x-2 text-sm">
                <span className="font-semibold text-foreground">{oferta.nombre}</span>
                {oferta.calificacion === null ? null : (
                  <span className="text-muted-foreground">★ {oferta.calificacion}</span>
                )}
                <span className="text-muted-foreground">{textoDeDisponibles(libres)}</span>
              </p>
            </div>
            {porFranja(oferta.slots).map((franja) => (
              <TimeSlotGroup
                key={franja.nombre}
                ofertaId={oferta.veterinarianId}
                veterinario={oferta.nombre}
                franja={franja.nombre}
                slots={franja.slots}
                veterinarianId={veterinarianId}
                scheduledAt={scheduledAt}
                durationMinutes={durationMinutes}
                onSelect={onSelect}
              />
            ))}
            {libres > 0 ? (
              <CustomTimeInput
                key={`${dia}-${String(oferta.veterinarianId)}`}
                veterinarianId={oferta.veterinarianId}
                veterinario={oferta.nombre}
                dia={dia}
                windows={oferta.windows}
                slots={oferta.slots}
                durationMinutes={durationMinutes}
                onSelect={onSelect}
              />
            ) : null}
          </li>
        )
      })}
    </ul>
  )
}
