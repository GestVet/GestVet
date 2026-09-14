import { useQuery } from '@tanstack/react-query'

import { clientsQueryKey, fetchClients } from '../../api/directory'
import type { UserResponse } from '../../api/types'
import DataTable, { type DataColumn } from '../../components/DataTable'
import PageHeader from '../../components/PageHeader'
import RowExpandButton from '../../components/RowExpandButton'
import StatusBadge from '../../components/StatusBadge'
import { useCan } from '../../store/session'
import ClientDetails from './ClientDetails'
import { hasPendingContact } from './clientContact'
import ClientStatusToggle from './ClientStatusToggle'

const COLUMNAS_BASE: readonly DataColumn<UserResponse>[] = [
  {
    id: 'nombre',
    header: 'Nombre',
    cell: (cliente) => `${cliente.first_name} ${cliente.last_name}`,
  },
  {
    id: 'correo',
    header: 'Correo',
    cell: (cliente) =>
      hasPendingContact(cliente) ? (
        <StatusBadge label="Correo pendiente" tone="pending" />
      ) : (
        cliente.email
      ),
  },
  { id: 'telefono', header: 'Teléfono', cell: (cliente) => cliente.phone || '—' },
  {
    id: 'estado',
    header: 'Estado',
    cell: (cliente) => (
      <StatusBadge
        label={cliente.is_active ? 'Activa' : 'Inactiva'}
        tone={cliente.is_active ? 'completed' : undefined}
      />
    ),
  },
  {
    id: 'mascotas',
    header: 'Mascotas',
    cell: (cliente, fila) => (
      <RowExpandButton
        isExpanded={fila.isExpanded}
        onToggle={fila.toggleExpanded}
        collapsedLabel={hasPendingContact(cliente) ? 'Ver mascotas y contacto' : 'Ver mascotas'}
        expandedLabel="Ocultar"
      />
    ),
  },
]

// Activar y desactivar cuentas es cosa de la administración. Un veterinario
// ve el padrón pero no lo modifica.
const COLUMNAS_ADMIN: readonly DataColumn<UserResponse>[] = [
  ...COLUMNAS_BASE,
  {
    id: 'acciones',
    header: 'Acciones',
    cell: (cliente) => <ClientStatusToggle clientId={cliente.id} isActive={cliente.is_active} />,
  },
]

export default function ClientsView() {
  const clientes = useQuery({ queryKey: clientsQueryKey, queryFn: fetchClients })
  const esAdmin = useCan('users.change_status')

  return (
    <div className="flex flex-col gap-6">
      <PageHeader title="Clientes" />
      <DataTable
        columns={esAdmin ? COLUMNAS_ADMIN : COLUMNAS_BASE}
        data={clientes.data?.items ?? []}
        isLoading={clientes.isPending}
        emptyMessage="Todavía no hay clientes registrados."
        getRowId={(cliente) => String(cliente.id)}
        pageSize={15}
        renderExpanded={(cliente) => <ClientDetails cliente={cliente} />}
      />
    </div>
  )
}
