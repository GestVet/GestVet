import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'

import {
  accessRolesQueryKey,
  fetchAccessRoles,
  fetchRoleAssignments,
  roleAssignmentsQueryKey,
} from '../../api/access'
import { fetchStaff, staffQueryKey } from '../../api/directory'
import type { AccessRoleResponse, UserResponse, UserRole } from '../../api/types'
import DataTable, { type DataColumn } from '../../components/DataTable'
import FormDialog from '../../components/FormDialog'
import Icon from '../../components/Icon'
import PageHeader from '../../components/PageHeader'
import SectionCard from '../../components/SectionCard'
import StatusBadge from '../../components/StatusBadge'
import { Button } from '../../components/ui/button'
import { useCan } from '../../store/session'
import StaffAccessRole from './StaffAccessRole'
import StaffForm from './StaffForm'
import StaffRowActions from './StaffRowActions'

const ETIQUETA_DE_ROL: Record<UserRole, string> = {
  admin: 'Administración',
  client: 'Cliente',
  veterinarian: 'Veterinario',
}

/** Roles y asignaciones, cuando quien mira puede cambiarlos. */
interface Accesos {
  readonly roles: readonly AccessRoleResponse[]
  readonly asignados: ReadonlyMap<number, number>
}

function columnaDeRol(accesos: Accesos | null): DataColumn<UserResponse> {
  if (accesos === null) {
    return { id: 'rol', header: 'Rol', cell: (cuenta) => ETIQUETA_DE_ROL[cuenta.role] }
  }
  return {
    id: 'rol',
    header: 'Rol',
    cell: (cuenta) => (
      <StaffAccessRole
        account={cuenta}
        roles={accesos.roles}
        assignedRoleId={accesos.asignados.get(cuenta.id)}
      />
    ),
  }
}

function columnas(accesos: Accesos | null): DataColumn<UserResponse>[] {
  return [
    { id: 'nombre', header: 'Nombre', cell: (cuenta) => `${cuenta.first_name} ${cuenta.last_name}` },
    { id: 'correo', header: 'Correo', cell: (cuenta) => cuenta.email },
    columnaDeRol(accesos),
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
}

function useAccesos(): Accesos | null {
  const puedeAsignar = useCan('roles.manage')
  const roles = useQuery({
    queryKey: accessRolesQueryKey,
    queryFn: fetchAccessRoles,
    enabled: puedeAsignar,
  })
  const asignaciones = useQuery({
    queryKey: roleAssignmentsQueryKey,
    queryFn: fetchRoleAssignments,
    enabled: puedeAsignar,
  })
  if (!puedeAsignar || roles.data === undefined || asignaciones.data === undefined) {
    return null
  }
  return {
    roles: roles.data.items,
    asignados: new Map(asignaciones.data.items.map((item) => [item.user_id, item.role_id])),
  }
}

export default function StaffView() {
  const personal = useQuery({ queryKey: staffQueryKey, queryFn: fetchStaff })
  const accesos = useAccesos()
  const [dandoDeAlta, setDandoDeAlta] = useState(false)

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Personal"
        description="Los veterinarios de la clínica, su rol y si su cuenta está activa."
        actions={
          <Button
            type="button"
            size="lg"
            className="h-10 px-4"
            onClick={() => {
              setDandoDeAlta(true)
            }}
          >
            <Icon name="agregar" size={16} />
            <span>Dar de alta</span>
          </Button>
        }
      />

      <FormDialog
        open={dandoDeAlta}
        onOpenChange={setDandoDeAlta}
        title="Dar de alta un veterinario"
        description="La cuenta queda activa con la contraseña inicial. Pídele que la cambie al entrar."
        size="lg"
      >
        <StaffForm
          onDone={() => {
            setDandoDeAlta(false)
          }}
        />
      </FormDialog>

      <SectionCard title="Equipo">
        <DataTable
          columns={columnas(accesos)}
          data={personal.data?.items ?? []}
          isLoading={personal.isPending}
          emptyMessage="Todavía no hay veterinarios registrados."
          getRowId={(cuenta) => String(cuenta.id)}
        />
      </SectionCard>
    </div>
  )
}
