import { Button } from '../../components/ui/button'
import type { TipoDeTurno } from './shiftSchema'

export interface HorarioRapido {
  readonly etiqueta: string
  readonly desde: string
  readonly hasta: string
  readonly kind: TipoDeTurno
}

// Los horarios que más se repiten en una veterinaria con atención de día y
// guardia de noche. Cargan horas y tipo de un toque; después se ajustan.
const HORARIOS: readonly HorarioRapido[] = [
  { etiqueta: 'Mañana', desde: '08:00', hasta: '14:00', kind: 'regular' },
  { etiqueta: 'Tarde', desde: '14:00', hasta: '20:00', kind: 'regular' },
  { etiqueta: 'Día completo', desde: '09:00', hasta: '18:00', kind: 'regular' },
  { etiqueta: 'Guardia de noche', desde: '20:00', hasta: '08:00', kind: 'on_call' },
  { etiqueta: 'Guardia de 24 h', desde: '08:00', hasta: '08:00', kind: 'on_call' },
]

interface ShiftPresetsProps {
  readonly id: string
  readonly desde: string
  readonly hasta: string
  readonly kind: TipoDeTurno
  readonly onElegir: (horario: HorarioRapido) => void
}

/** Botones con los horarios de siempre; el que coincide con lo cargado queda marcado. */
export default function ShiftPresets({ id, desde, hasta, kind, onElegir }: ShiftPresetsProps) {
  return (
    <fieldset
      className="m-0 flex flex-col gap-2 border-0 p-0 sm:col-span-2"
      aria-describedby={`${id}-ayuda`}
    >
      <legend className="mb-1 text-sm font-medium">Horario rápido</legend>
      <div className="flex flex-wrap gap-2">
        {HORARIOS.map((horario) => {
          const elegido =
            horario.desde === desde && horario.hasta === hasta && horario.kind === kind
          return (
            <Button
              key={horario.etiqueta}
              type="button"
              size="sm"
              variant={elegido ? 'default' : 'outline'}
              aria-pressed={elegido}
              onClick={() => {
                onElegir(horario)
              }}
            >
              <span>{horario.etiqueta}</span>
              <span className="text-xs tabular-nums opacity-80">
                {horario.desde}–{horario.hasta}
              </span>
            </Button>
          )
        })}
      </div>
      <p id={`${id}-ayuda`} className="m-0 text-xs text-muted-foreground">
        Carga las horas y el tipo. Puedes ajustarlos abajo.
      </p>
    </fieldset>
  )
}
