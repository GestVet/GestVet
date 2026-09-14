import StatusBadge, { type StatusTone } from './StatusBadge'
import { formatearFechaDeVacuna } from './vaccineDates'

/** Forma mínima del estado de una vacuna; un componente compartido no depende de `api`. */
export interface VaccineStatusLike {
  readonly vaccine: string
  readonly label: string
  readonly last_applied_on: string
  readonly next_due_on: string | null
  readonly status: 'overdue' | 'due_soon' | 'up_to_date' | 'no_booster'
  readonly status_label: string
}

const TONO: Record<VaccineStatusLike['status'], StatusTone | undefined> = {
  overdue: 'cancelled',
  due_soon: 'pending',
  up_to_date: 'completed',
  no_booster: undefined,
}

interface VaccineStatusListProps {
  readonly summary: readonly VaccineStatusLike[]
}

/** Una tarjeta por vacuna con su estado, lo vencido primero: se lee de un vistazo. */
export default function VaccineStatusList({ summary }: VaccineStatusListProps) {
  return (
    <ul className="m-0 grid list-none gap-3 p-0 sm:grid-cols-2 xl:grid-cols-3">
      {summary.map((vacuna) => (
        <li
          key={`${vacuna.vaccine}-${vacuna.label}`}
          className="flex flex-col gap-1.5 rounded-lg border bg-card p-3"
        >
          <div className="flex items-start justify-between gap-2">
            <span className="font-medium">{vacuna.label}</span>
            <StatusBadge label={vacuna.status_label} tone={TONO[vacuna.status]} />
          </div>
          <span className="text-sm text-muted-foreground">
            Última dosis: {formatearFechaDeVacuna(vacuna.last_applied_on)}
          </span>
          <span className="text-sm text-muted-foreground">
            {vacuna.next_due_on === null
              ? 'No lleva refuerzo'
              : `Próxima dosis: ${formatearFechaDeVacuna(vacuna.next_due_on)}`}
          </span>
        </li>
      ))}
    </ul>
  )
}
