import { Button } from '../../components/ui/button'
import { formatearHora } from '../../services/clinicTime'

interface TimeSlotGroupProps {
  /** Veterinario al que pertenecen estas horas. */
  readonly ofertaId: number
  readonly veterinario: string
  /** Mañana, tarde o noche. */
  readonly franja: string
  readonly horas: readonly string[]
  /** La elección actual del formulario. */
  readonly veterinarianId: number
  readonly scheduledAt: string
  readonly onSelect: (veterinarianId: number, time: string) => void
}

/** Las horas libres de un veterinario en una parte del día. */
export default function TimeSlotGroup({
  ofertaId,
  veterinario,
  franja,
  horas,
  veterinarianId,
  scheduledAt,
  onSelect,
}: TimeSlotGroupProps) {
  return (
    <div className="flex flex-col gap-1.5">
      <p className="m-0 text-xs font-medium text-muted-foreground">{franja}</p>
      <div
        role="group"
        aria-label={`${franja}, horas libres con ${veterinario}`}
        className="flex flex-wrap gap-2"
      >
        {horas.map((time) => {
          const elegida = ofertaId === veterinarianId && time === scheduledAt
          return (
            <Button
              key={time}
              type="button"
              size="sm"
              variant={elegida ? 'default' : 'outline'}
              aria-pressed={elegida}
              className="h-9 min-w-20 px-3 tabular-nums"
              onClick={() => {
                onSelect(ofertaId, time)
              }}
            >
              {formatearHora(time)}
            </Button>
          )
        })}
      </div>
    </div>
  )
}
