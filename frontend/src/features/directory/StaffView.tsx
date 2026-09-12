import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'

import { fetchStaff, staffQueryKey } from '../../api/directory'
import type { UserRole } from '../../api/types'
import FormMessage from '../../components/FormMessage'
import StatusBadge from '../../components/StatusBadge'
import TableShell from '../../components/TableShell'
import { errorMessage } from '../../services/api'
import StaffForm from './StaffForm'
import StaffRowActions from './StaffRowActions'

const COLUMNAS = ['Nombre', 'Correo', 'Rol', 'Respaldo', 'Estado', 'Acciones'] as const

const ETIQUETA_DE_ROL: Record<UserRole, string> = {
  admin: 'Administración',
  client: 'Cliente',
  veterinarian: 'Veterinario',
  emergency_veterinarian: 'Veterinario de guardia',
}

export default function StaffView() {
  const personal = useQuery({ queryKey: staffQueryKey, queryFn: fetchStaff })
  const [fallo, setFallo] = useState<unknown>(null)

  const items = personal.data?.items ?? []

  return (
    <div className="stack">
      <div className="page-header">
        <h1>Personal</h1>
      </div>

      <StaffForm />

      <section className="card">
        <h2>Equipo</h2>
        {fallo === null ? null : (
          <FormMessage tone="error">
            {errorMessage(fallo, 'No se pudo actualizar la cuenta.')}
          </FormMessage>
        )}

        <TableShell
          columns={COLUMNAS}
          isLoading={personal.isPending}
          isEmpty={items.length === 0}
          emptyMessage="Todavía no hay veterinarios registrados."
        >
          {items.map((cuenta) => (
            <tr key={cuenta.id}>
              <td>
                {cuenta.first_name} {cuenta.last_name}
              </td>
              <td>{cuenta.email}</td>
              <td>{ETIQUETA_DE_ROL[cuenta.role]}</td>
              <td>
                {cuenta.role === 'veterinarian' && cuenta.can_cover_emergencies ? (
                  <StatusBadge label="Habilitado" tone="confirmed" />
                ) : (
                  '—'
                )}
              </td>
              <td>
                <StatusBadge
                  label={cuenta.is_active ? 'Activa' : 'Inactiva'}
                  tone={cuenta.is_active ? 'completed' : undefined}
                />
              </td>
              <td>
                <StaffRowActions account={cuenta} onError={setFallo} />
              </td>
            </tr>
          ))}
        </TableShell>
      </section>
    </div>
  )
}
