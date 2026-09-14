import type { ReactNode } from 'react'

import DataTable, { type DataColumn } from './DataTable'
import EmptyState from './EmptyState'
import SectionHeading from './SectionHeading'
import { formatearFechaDeVacuna } from './vaccineDates'
import VaccineStatusList, { type VaccineStatusLike } from './VaccineStatusList'

interface VaccinationLike {
  readonly id: number
  readonly vaccine_label: string
  readonly applied_on: string
  readonly next_due_on: string | null
  readonly product_name: string
  readonly batch: string
  readonly notes: string
}

const COLUMNAS: readonly DataColumn<VaccinationLike>[] = [
  { id: 'fecha', header: 'Aplicada', cell: (vacuna) => formatearFechaDeVacuna(vacuna.applied_on) },
  { id: 'vacuna', header: 'Vacuna', className: 'min-w-40 whitespace-normal', cell: (vacuna) => vacuna.vaccine_label },
  {
    id: 'producto',
    header: 'Producto y lote',
    className: 'min-w-40 whitespace-normal',
    cell: (vacuna) =>
      [vacuna.product_name, vacuna.batch === '' ? '' : `Lote ${vacuna.batch}`]
        .filter(Boolean)
        .join(' · ') || '—',
  },
  {
    id: 'proxima',
    header: 'Próxima dosis',
    cell: (vacuna) =>
      vacuna.next_due_on === null ? '—' : formatearFechaDeVacuna(vacuna.next_due_on),
  },
  {
    id: 'notas',
    header: 'Notas',
    className: 'min-w-48 whitespace-normal text-muted-foreground',
    cell: (vacuna) => vacuna.notes || '—',
  },
]

interface VaccinationCardProps {
  readonly summary: readonly VaccineStatusLike[]
  readonly items: readonly VaccinationLike[]
  readonly isLoading: boolean
  /** Botones a la derecha del título, como registrar una vacuna. */
  readonly actions?: ReactNode
}

/**
 * El carnet de vacunas de una mascota.
 *
 * Arriba, el estado de cada vacuna según su última dosis, lo vencido primero;
 * abajo, todas las aplicaciones con producto y lote. Lo usan el dueño, en modo
 * lectura, y el personal, que además registra.
 */
export default function VaccinationCard({ summary, items, isLoading, actions }: VaccinationCardProps) {
  const vacio = isLoading || items.length === 0

  return (
    <section className="flex flex-col gap-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <SectionHeading as="h3" description="Qué vacunas tiene y cuándo le toca la siguiente dosis.">
          Carnet de vacunas
        </SectionHeading>
        {actions}
      </div>
      {vacio ? (
        <EmptyState title={isLoading ? 'Cargando el carnet…' : 'Todavía no hay vacunas registradas.'} />
      ) : (
        <>
          <VaccineStatusList summary={summary} />
          <DataTable
            columns={COLUMNAS}
            data={items}
            isLoading={false}
            emptyMessage="Todavía no hay vacunas registradas."
            getRowId={(vacuna) => String(vacuna.id)}
            pageSize={10}
          />
        </>
      )}
    </section>
  )
}
