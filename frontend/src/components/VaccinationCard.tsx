import type { ReactNode } from 'react'

import CollapsibleSection from './CollapsibleSection'
import DataTable, { type DataColumn } from './DataTable'
import EmptyState from './EmptyState'
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
  /** Cuándo se le avisó al dueño por WhatsApp que se acerca la próxima dosis. */
  readonly reminder_sent_at?: string | null
}

const FORMATO_AVISO = new Intl.DateTimeFormat('es-PE', { dateStyle: 'medium' })

function textoDelAviso(vacuna: VaccinationLike): string {
  const enviado = vacuna.reminder_sent_at ?? null
  return enviado === null ? '' : `Aviso por WhatsApp el ${FORMATO_AVISO.format(new Date(enviado))}`
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
    className: 'whitespace-normal',
    cell: (vacuna) =>
      vacuna.next_due_on === null ? (
        '—'
      ) : (
        <span className="flex flex-col">
          {formatearFechaDeVacuna(vacuna.next_due_on)}
          <span className="text-xs text-muted-foreground">{textoDelAviso(vacuna)}</span>
        </span>
      ),
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
    <CollapsibleSection
      title="Carnet de vacunas"
      description="Qué vacunas tiene y cuándo le toca la siguiente dosis."
      actions={actions}
    >
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
    </CollapsibleSection>
  )
}
