import { useQuery } from '@tanstack/react-query'

import { fetchStaff, staffQueryKey } from '../../api/directory'
import type { UserResponse, UserRole } from '../../api/types'
import DataTable, { type DataColumn } from '../../components/DataTable'
import PageHeader from '../../components/PageHeader'
import SectionCard from '../../components/SectionCard'
import StatusBadge from '../../components/StatusBadge'
import StaffForm from './StaffForm'
import StaffRowActions from './StaffRowActions'

const ETIQUETA_DE_ROL: Record<UserRole, string> = {
  admin: 'Administración',
  client: 'Cliente',
  veterinarian: 'Veterinario',
  emergency_veterinarian: 'Veterinario de guardia',
}

const COLUMNAS: readonly DataColumn<UserResponse>[] = [
  { id: 'nombre', header: 'Nombre', cell: (cuenta) => `${cuenta.first_name} ${cuenta.last_name}` },
  { id: 'correo', header: 'Correo', cell: (cuenta) => cuenta.email },
  { id: 'rol', header: 'Rol', cell: (cuenta) => ETIQUETA_DE_ROL[cuenta.role] },
  {
    id: 'respaldo',
    header: 'Respaldo',
    cell: (cuenta) =>
      cuenta.role === 'veterinarian' && cuenta.can_cover_emergencies ? (
        <StatusBadge label="Habilitado" tone="confirmed" />
      ) : (
        '—'
      ),
  },
  {
    id: 'estado',
    header: 'Estado',
    cell: (cuenta) => (
      <StatusBadge
        label={cuenta.is_active ? 'Activa' : 'Inactiva'}
        tone={cuenta.is_active ? 'completed' : undefined}
      />
    ),
  },
  { id: 'acciones', header: 'Acciones', cell: (cuenta) => <StaffRowActions account={cuenta} /> },
]

export default function StaffView() {
  const personal = useQuery({ queryKey: staffQueryKey, queryFn: fetchStaff })

  return (
    <div className="flex flex-col gap-6">
      <PageHeader title="Personal" />

      <StaffForm />

      <SectionCard title="Equipo">
        <DataTable
          columns={COLUMNAS}
          data={personal.data?.items ?? []}
          isLoading={personal.isPending}
          emptyMessage="Todavía no hay veterinarios registrados."
          getRowId={(cuenta) => String(cuenta.id)}
        />
      </SectionCard>
    </div>
  )
}
