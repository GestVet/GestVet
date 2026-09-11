import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'

import { activityQueryKey, fetchActivity } from '../../api/directory'
import type { UserRole } from '../../api/types'
import StatusBadge from '../../components/StatusBadge'
import TableShell from '../../components/TableShell'

const COLUMNAS = ['Cuándo', 'Quién', 'Rol', 'Qué hizo', 'Detalle'] as const

const ETIQUETA_DE_ROL: Record<UserRole, string> = {
  admin: 'Administración',
  client: 'Cliente',
  veterinarian: 'Veterinario',
  emergency_veterinarian: 'Veterinario de guardia',
}

const FILTROS: readonly { readonly value: string; readonly label: string }[] = [
  { value: '', label: 'Todos los roles' },
  { value: 'client', label: 'Clientes' },
  { value: 'veterinarian', label: 'Veterinarios' },
  { value: 'emergency_veterinarian', label: 'Veterinarios de guardia' },
  { value: 'admin', label: 'Administración' },
]

const FORMATO = new Intl.DateTimeFormat('es-PE', { dateStyle: 'medium', timeStyle: 'short' })

export default function ActivityView() {
  const [rol, setRol] = useState('')
  const movimientos = useQuery({
    queryKey: activityQueryKey(rol),
    queryFn: () => fetchActivity(rol),
  })

  const items = movimientos.data?.items ?? []

  return (
    <div className="stack">
      <div className="page-header">
        <div>
          <h1>Movimientos</h1>
          <p className="muted">
            Qué hizo cada cuenta y cuándo. Incluye las acciones de la administración.
          </p>
        </div>
        <div className="field">
          <label htmlFor="rol">Filtrar por rol</label>
          <select
            id="rol"
            value={rol}
            onChange={(evento) => {
              setRol(evento.target.value)
            }}
          >
            {FILTROS.map((filtro) => (
              <option key={filtro.value} value={filtro.value}>
                {filtro.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <section className="card">
        <TableShell
          columns={COLUMNAS}
          isLoading={movimientos.isPending}
          isEmpty={items.length === 0}
          emptyMessage="Todavía no hay movimientos registrados."
        >
          {items.map((movimiento) => (
            <tr key={movimiento.id}>
              <td>{FORMATO.format(new Date(movimiento.occurred_at))}</td>
              <td>{movimiento.user_name}</td>
              <td>
                <StatusBadge
                  label={ETIQUETA_DE_ROL[movimiento.user_role]}
                  tone={movimiento.user_role === 'admin' ? 'confirmed' : undefined}
                />
              </td>
              <td>{movimiento.kind_label}</td>
              <td className="muted">{movimiento.detail}</td>
            </tr>
          ))}
        </TableShell>
      </section>
    </div>
  )
}
