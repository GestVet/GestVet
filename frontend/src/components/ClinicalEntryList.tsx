import AttachmentsPanel from './AttachmentsPanel'
import ClinicalHistoryReportButton from './ClinicalHistoryReportButton'
import DataTable, { type DataColumn } from './DataTable'
import RowExpandButton from './RowExpandButton'
import SectionHeading from './SectionHeading'

// Las celdas de texto libre pueden partirse; las demas no.
const TEXTO_LARGO = 'min-w-48 whitespace-normal'

const FORMATO = new Intl.DateTimeFormat('es-PE', { dateStyle: 'medium', timeStyle: 'short' })

interface AttachmentLike {
  readonly id: number
  readonly filename: string
  readonly url: string
}

/**
 * Forma mínima que este componente necesita. No importa el tipo del contrato
 * generado a propósito: un componente compartido no puede depender de `api`,
 * así que describe la forma que usa y el tipado estructural hace el resto.
 */
interface ClinicalEntryLike {
  readonly id: number
  readonly occurred_at: string
  readonly kind_label: string
  readonly diagnosis: string
  readonly treatment: string
  readonly weight_kg: string | null
  readonly notes: string
  readonly attachments: readonly AttachmentLike[]
}

const COLUMNAS: readonly DataColumn<ClinicalEntryLike>[] = [
  { id: 'fecha', header: 'Fecha', cell: (entrada) => FORMATO.format(new Date(entrada.occurred_at)) },
  { id: 'tipo', header: 'Tipo', cell: (entrada) => entrada.kind_label },
  {
    id: 'diagnostico',
    header: 'Diagnóstico',
    className: TEXTO_LARGO,
    cell: (entrada) => entrada.diagnosis || '—',
  },
  {
    id: 'tratamiento',
    header: 'Tratamiento',
    className: TEXTO_LARGO,
    cell: (entrada) => entrada.treatment || '—',
  },
  {
    id: 'peso',
    header: 'Peso',
    cell: (entrada) => (entrada.weight_kg ? `${entrada.weight_kg} kg` : '—'),
  },
  {
    id: 'notas',
    header: 'Notas',
    className: TEXTO_LARGO,
    cell: (entrada) => entrada.notes,
  },
  {
    id: 'adjuntos',
    header: 'Adjuntos',
    cell: (entrada, fila) => (
      <RowExpandButton
        isExpanded={fila.isExpanded}
        onToggle={fila.toggleExpanded}
        collapsedLabel={`Ver adjuntos (${String(entrada.attachments.length)})`}
        expandedLabel="Ocultar adjuntos"
      />
    ),
  },
]

interface ClinicalEntryListProps {
  readonly items: readonly ClinicalEntryLike[]
  readonly isLoading: boolean
  readonly petId: number
  readonly canManageAttachments: boolean
}

/**
 * Lista de la historia clínica de una mascota.
 *
 * Puramente presentacional: no pide los datos, los recibe. Así la usan tanto
 * la vista del cliente (solo lectura) como la del personal (con el
 * formulario de carga al lado), sin que ninguna de las dos características
 * tenga que importar a la otra.
 */
export default function ClinicalEntryList({
  items,
  isLoading,
  petId,
  canManageAttachments,
}: ClinicalEntryListProps) {
  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <SectionHeading as="h3">Historia clínica</SectionHeading>
        <ClinicalHistoryReportButton petId={petId} />
      </div>
      <DataTable
        columns={COLUMNAS}
        data={items}
        isLoading={isLoading}
        emptyMessage="Todavía no hay entradas en la historia clínica."
        getRowId={(entrada) => String(entrada.id)}
        renderExpanded={(entrada) => (
          <AttachmentsPanel
            clinicalEntryId={entrada.id}
            petId={petId}
            attachments={entrada.attachments}
            canManage={canManageAttachments}
          />
        )}
      />
    </div>
  )
}
