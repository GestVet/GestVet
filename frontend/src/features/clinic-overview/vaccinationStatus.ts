import type { PetOverviewResponse } from '../../api/types'

export type VaccinationStatusCode = PetOverviewResponse['vaccination_status']

/**
 * Un color por estado, tomado de los tokens que ya existen en index.css — el
 * mismo significado que ya tienen en el resto de la app (éxito, alerta,
 * error), ninguno inventado para este gráfico.
 */
export const VACCINATION_STATUSES: readonly {
  value: VaccinationStatusCode
  label: string
  color: string
  textClassName: string
}[] = [
  {
    value: 'overdue',
    label: 'Vencida',
    color: 'var(--destructive)',
    textClassName: 'text-destructive',
  },
  {
    value: 'due_soon',
    label: 'Vence pronto',
    color: 'var(--warning)',
    textClassName: 'text-warning',
  },
  {
    value: 'up_to_date',
    label: 'Al día',
    color: 'var(--success)',
    textClassName: 'text-success',
  },
  {
    value: 'no_vaccines',
    label: 'Sin vacunas',
    color: 'var(--muted-foreground)',
    textClassName: 'text-muted-foreground',
  },
]

export function vaccinationStatusMeta(status: VaccinationStatusCode) {
  return VACCINATION_STATUSES.find((item) => item.value === status) ?? VACCINATION_STATUSES[3]
}
