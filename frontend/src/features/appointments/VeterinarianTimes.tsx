import { formatearHora24 } from '../../services/clinicTime'
import TimeSlotGroup from './TimeSlotGroup'

export interface OfertaDeVeterinario {
  readonly veterinarianId: number
  readonly nombre: string
  readonly calificacion: string | null
  readonly times: readonly string[]
}

interface VeterinarianTimesProps {
  readonly ofertas: readonly OfertaDeVeterinario[]
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

function porFranja(times: readonly string[]) {
  return FRANJAS.map((franja) => ({
    nombre: franja.nombre,
    horas: times.filter((time) => horaDelDia(time) >= franja.desde && horaDelDia(time) < franja.hasta),
  })).filter((franja) => franja.horas.length > 0)
}

function iniciales(nombre: string): string {
  return nombre
    .split(' ')
    .filter((parte) => parte !== '')
    .slice(0, 2)
    .map((parte) => parte.charAt(0).toUpperCase())
    .join('')
}

function horasLibres(cantidad: number): string {
  return cantidad === 1 ? '1 hora libre' : `${String(cantidad)} horas libres`
}

/**
 * Los veterinarios con horas libres en el dia elegido, cada uno con sus horas.
 *
 * Con un solo veterinario es una lista de horas; con varios, la persona puede
 * elegir por hora o por profesional sin cambiar de pantalla.
 */
export default function VeterinarianTimes({
  ofertas,
  veterinarianId,
  scheduledAt,
  onSelect,
}: VeterinarianTimesProps) {
  return (
    <ul className="m-0 grid list-none gap-3 p-0">
      {ofertas.map((oferta) => (
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
              <span className="text-muted-foreground">{horasLibres(oferta.times.length)}</span>
            </p>
          </div>
          {porFranja(oferta.times).map((franja) => (
            <TimeSlotGroup
              key={franja.nombre}
              ofertaId={oferta.veterinarianId}
              veterinario={oferta.nombre}
              franja={franja.nombre}
              horas={franja.horas}
              veterinarianId={veterinarianId}
              scheduledAt={scheduledAt}
              onSelect={onSelect}
            />
          ))}
        </li>
      ))}
    </ul>
  )
}
