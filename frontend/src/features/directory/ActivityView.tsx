import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { useState } from 'react'

import { activityQueryKey, fetchActivity } from '../../api/directory'
import type { UserRole } from '../../api/types'
import DataTable, { type DataColumn } from '../../components/DataTable'
import FieldIcon from '../../components/FieldIcon'
import PageHeader from '../../components/PageHeader'
import StatusBadge from '../../components/StatusBadge'
import { Label } from '../../components/ui/label'
import { NativeSelect, NativeSelectOption } from '../../components/ui/native-select'

type Movimiento = Awaited<ReturnType<typeof fetchActivity>>['items'][number]

const ETIQUETA_DE_ROL: Record<UserRole, string> = {
  admin: 'Administración',
  client: 'Cliente',
  veterinarian: 'Veterinario',
}

const FILTROS: readonly { readonly value: string; readonly label: string }[] = [
  { value: '', label: 'Todos los roles' },
  { value: 'client', label: 'Clientes' },
  { value: 'veterinarian', label: 'Veterinarios' },
  { value: 'admin', label: 'Administración' },
]

const FORMATO = new Intl.DateTimeFormat('es-PE', { dateStyle: 'medium', timeStyle: 'short' })

const COLUMNAS: readonly DataColumn<Movimiento>[] = [
  { id: 'cuando', header: 'Cuándo', cell: (m) => FORMATO.format(new Date(m.occurred_at)) },
  { id: 'quien', header: 'Quién', cell: (m) => m.user_name },
  {
    id: 'rol',
    header: 'Rol',
    cell: (m) => (
      <StatusBadge
        label={ETIQUETA_DE_ROL[m.user_role]}
        tone={m.user_role === 'admin' ? 'confirmed' : undefined}
      />
    ),
  },
  { id: 'que', header: 'Qué hizo', cell: (m) => m.kind_label },
  {
    id: 'detalle',
    header: 'Detalle',
    className: 'min-w-64 whitespace-normal text-muted-foreground',
    cell: (m) => m.detail,
  },
]

export default function ActivityView() {
  const [rol, setRol] = useState('')
  const movimientos = useQuery({
    queryKey: activityQueryKey(rol),
    queryFn: () => fetchActivity(rol),
    // Cambiar de rol deja las filas anteriores hasta que llegan las nuevas.
    placeholderData: keepPreviousData,
  })

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Movimientos"
        description="Qué hizo cada cuenta y cuándo. Incluye las acciones de la administración."
        actions={
          <div className="flex min-w-56 flex-col gap-2">
            <Label htmlFor="rol">Filtrar por rol</Label>
            <FieldIcon icon="filtro">
            <NativeSelect
              id="rol"
              className="w-full [&_select]:h-10"
              value={rol}
              onChange={(evento) => {
                setRol(evento.target.value)
              }}
            >
              {FILTROS.map((filtro) => (
                <NativeSelectOption key={filtro.value} value={filtro.value}>
                  {filtro.label}
                </NativeSelectOption>
              ))}
            </NativeSelect>
            </FieldIcon>
          </div>
        }
      />

      <DataTable
        columns={COLUMNAS}
        data={movimientos.data?.items ?? []}
        isLoading={movimientos.isPending}
        emptyMessage="Todavía no hay movimientos registrados."
        getRowId={(m) => String(m.id)}
        pageSize={25}
      />
    </div>
  )
}
