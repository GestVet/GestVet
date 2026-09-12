import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'

import { changeUserStatus, clientsQueryKey, fetchClients } from '../../api/directory'
import FormMessage from '../../components/FormMessage'
import TableShell from '../../components/TableShell'
import { errorMessage } from '../../services/api'
import { useIsAdmin } from '../../store/session'
import ClientRow from './ClientRow'

const COLUMNAS_BASE = ['Nombre', 'Correo', 'Teléfono', 'Estado', 'Mascotas'] as const

export default function ClientsView() {
  const queryClient = useQueryClient()
  const clientes = useQuery({ queryKey: clientsQueryKey, queryFn: fetchClients })
  const [expandido, setExpandido] = useState<number | null>(null)

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
            <ClientRow
              key={cliente.id}
              cliente={cliente}
              expandido={expandido === cliente.id}
              onToggle={() => {
                setExpandido(expandido === cliente.id ? null : cliente.id)
              }}
              puedeActivar={puedeActivar}
              cambiandoEstado={estado.isPending}
              onCambiarEstado={() => {
                estado.mutate({ id: cliente.id, activo: !cliente.is_active })
              }}
            />
          ))}
        </TableShell>
      </section>
    </div>
  )
}
