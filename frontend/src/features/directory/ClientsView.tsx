import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { changeUserStatus, clientsQueryKey, fetchClients } from '../../api/directory'
import FormMessage from '../../components/FormMessage'
import StatusBadge from '../../components/StatusBadge'
import TableShell from '../../components/TableShell'
import { errorMessage } from '../../services/api'
import { useIsAdmin } from '../../store/session'

const COLUMNAS_BASE = ['Nombre', 'Correo', 'Teléfono', 'Estado'] as const

export default function ClientsView() {
  const queryClient = useQueryClient()
  const clientes = useQuery({ queryKey: clientsQueryKey, queryFn: fetchClients })

  const estado = useMutation({
    mutationFn: ({ id, activo }: { id: number; activo: boolean }) => changeUserStatus(id, activo),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: clientsQueryKey })
    },
  })

  // Activar y desactivar cuentas es cosa de la administración. Un veterinario
  // ve el padrón pero no lo modifica.
  const puedeActivar = useIsAdmin()
  const columnas = puedeActivar ? [...COLUMNAS_BASE, 'Acciones'] : COLUMNAS_BASE
  const items = clientes.data?.items ?? []

  return (
    <div className="stack">
      <div className="page-header">
        <h1>Clientes</h1>
      </div>

      <section className="card">
        {estado.isError ? (
          <FormMessage tone="error">
            {errorMessage(estado.error, 'No se pudo actualizar la cuenta.')}
          </FormMessage>
        ) : null}

        <TableShell
          columns={columnas}
          isLoading={clientes.isPending}
          isEmpty={items.length === 0}
          emptyMessage="Todavía no hay clientes registrados."
        >
          {items.map((cliente) => (
            <tr key={cliente.id}>
              <td>
                {cliente.first_name} {cliente.last_name}
              </td>
              <td>{cliente.email}</td>
              <td>{cliente.phone || '—'}</td>
              <td>
                <StatusBadge
                  label={cliente.is_active ? 'Activa' : 'Inactiva'}
                  tone={cliente.is_active ? 'completed' : undefined}
                />
              </td>
              {puedeActivar ? (
                <td>
                  <button
                    type="button"
                    className={cliente.is_active ? 'btn btn-plain' : 'btn btn-green'}
                    disabled={estado.isPending}
                    onClick={() => {
                      estado.mutate({ id: cliente.id, activo: !cliente.is_active })
                    }}
                  >
                    {cliente.is_active ? 'Desactivar' : 'Activar'}
                  </button>
                </td>
              ) : null}
            </tr>
          ))}
        </TableShell>
      </section>
    </div>
  )
}
