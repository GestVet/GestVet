import ClinicalEntryRow from './ClinicalEntryRow'
import TableShell from './TableShell'

const COLUMNAS = [
  'Fecha',
  'Tipo',
  'Diagnóstico',
  'Tratamiento',
  'Peso',
  'Notas',
  'Adjuntos',
] as const

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
    <TableShell
      columns={COLUMNAS}
      isLoading={isLoading}
      isEmpty={items.length === 0}
      emptyMessage="Todavía no hay entradas en la historia clínica."
    >
      {items.map((entrada) => (
        <ClinicalEntryRow
          key={entrada.id}
          entrada={entrada}
          petId={petId}
          canManageAttachments={canManageAttachments}
        />
      ))}
    </TableShell>
  )
}
