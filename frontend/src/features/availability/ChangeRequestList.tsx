import type { ReactNode } from 'react'

import type { ChangeRequestResponse, ChangeRequestStatus } from '../../api/types'
import DataTable, { type DataColumn } from '../../components/DataTable'
import StatusBadge, { type StatusTone } from '../../components/StatusBadge'
import { CLINIC_TIME_ZONE } from '../../services/clinicTime'

const ESTADOS: Record<ChangeRequestStatus, { readonly label: string; readonly tone: StatusTone }> = {
  pending: { label: 'Pendiente', tone: 'pending' },
  accepted: { label: 'Aceptado', tone: 'completed' },
  rejected: { label: 'Rechazado', tone: 'cancelled' },
}

const FECHA = new Intl.DateTimeFormat('es-PE', {
  timeZone: CLINIC_TIME_ZONE,
  dateStyle: 'medium',
  timeStyle: 'short',
})

type Pedido = ChangeRequestResponse

interface ChangeRequestListProps {
  readonly pedidos: readonly Pedido[]
  readonly isLoading: boolean
  readonly emptyMessage: string
  /** Con nombres, la lista muestra de quién es cada pedido. */
  readonly nombreDe?: (veterinarianId: number) => string
  readonly renderActions?: (pedido: Pedido) => ReactNode
}

function columnas(
  nombreDe: ChangeRequestListProps['nombreDe'],
  renderActions: ChangeRequestListProps['renderActions'],
): DataColumn<Pedido>[] {
  const quien: DataColumn<Pedido>[] =
    nombreDe === undefined
      ? []
      : [{ id: 'veterinario', header: 'Veterinario', cell: (p) => nombreDe(p.veterinarian_id) }]
  const acciones: DataColumn<Pedido>[] =
    renderActions === undefined ? [] : [{ id: 'acciones', header: 'Acciones', cell: renderActions }]
  return [
    { id: 'fecha', header: 'Pedido el', cell: (p) => FECHA.format(new Date(p.created_at)) },
    ...quien,
    { id: 'mensaje', header: 'Qué pide', className: 'min-w-64 whitespace-normal', cell: (p) => p.message },
    {
      id: 'estado',
      header: 'Estado',
      cell: (p) => <StatusBadge label={ESTADOS[p.status].label} tone={ESTADOS[p.status].tone} />,
    },
    {
      id: 'respuesta',
      header: 'Respuesta',
      className: 'min-w-48 whitespace-normal text-muted-foreground',
      cell: (p) => (p.response === '' ? '—' : p.response),
    },
    ...acciones,
  ]
}

export default function ChangeRequestList({
  pedidos,
  isLoading,
  emptyMessage,
  nombreDe,
  renderActions,
}: ChangeRequestListProps) {
  return (
    <DataTable
      columns={columnas(nombreDe, renderActions)}
      data={[...pedidos]}
      isLoading={isLoading}
      emptyMessage={emptyMessage}
      getRowId={(pedido) => String(pedido.id)}
    />
  )
}
