import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'

import {
  accessRolesQueryKey,
  fetchAccessRoles,
  fetchPermissionCatalog,
  permissionCatalogQueryKey,
} from '../../api/access'
import type { AccessRoleResponse } from '../../api/types'
import DataTable, { type DataColumn } from '../../components/DataTable'
import Icon from '../../components/Icon'
import PageHeader from '../../components/PageHeader'
import SectionCard from '../../components/SectionCard'
import StatusBadge from '../../components/StatusBadge'
import { Button } from '../../components/ui/button'
import RoleEditor from './RoleEditor'
import RoleRowActions from './RoleRowActions'
import { ETIQUETA_DE_TIPO } from './roleSchema'

type Edicion = AccessRoleResponse | 'nuevo' | null

function columnas(onEdit: (role: AccessRoleResponse) => void): DataColumn<AccessRoleResponse>[] {
  return [
    {
      id: 'nombre',
      header: 'Rol',
      className: 'min-w-56 whitespace-normal',
      cell: (rol) => (
        <div className="flex flex-col gap-1">
          <span className="flex flex-wrap items-center gap-2 font-medium">
            {rol.name}
            {rol.is_system ? <StatusBadge label="Por defecto" tone="confirmed" /> : null}
          </span>
          {rol.description === '' ? null : (
            <span className="text-sm text-muted-foreground">{rol.description}</span>
          )}
        </div>
      ),
    },
    { id: 'tipo', header: 'Tipo de cuenta', cell: (rol) => ETIQUETA_DE_TIPO[rol.account_kind] },
    { id: 'permisos', header: 'Permisos', cell: (rol) => String(rol.permissions.length) },
    {
      id: 'cuentas',
      header: 'Cuentas',
      cell: (rol) =>
        rol.is_system ? 'Las que no tienen otro rol' : String(rol.assigned_count),
    },
    { id: 'acciones', header: 'Acciones', cell: (rol) => <RoleRowActions role={rol} onEdit={onEdit} /> },
  ]
}

function tituloDe(edicion: Exclude<Edicion, null>): string {
  return edicion === 'nuevo' ? 'Nuevo rol' : `Editar «${edicion.name}»`
}

/**
 * Roles y permisos de la clínica.
 *
 * Cada tipo de cuenta tiene un rol por defecto; la administración puede
 * ajustarle los permisos o crear roles nuevos y asignarlos desde Personal.
 * Los cambios llegan en el momento a las cuentas afectadas.
 */
export default function RolesView() {
  const catalogo = useQuery({
    queryKey: permissionCatalogQueryKey,
    queryFn: fetchPermissionCatalog,
    // El catálogo vive en el código del servidor: no cambia sin un despliegue.
    staleTime: Infinity,
  })
  const roles = useQuery({ queryKey: accessRolesQueryKey, queryFn: fetchAccessRoles })
  const [edicion, setEdicion] = useState<Edicion>(null)

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Roles y permisos"
        description="Qué puede hacer cada cuenta. Quien pierde un permiso deja de ver esa parte al instante."
        actions={
          <Button
            type="button"
            size="lg"
            className="h-10 px-4"
            onClick={() => {
              setEdicion('nuevo')
            }}
          >
            <Icon name="agregar" size={16} />
            <span>Nuevo rol</span>
          </Button>
        }
      />

      {edicion === null || catalogo.data === undefined ? null : (
        <SectionCard title={tituloDe(edicion)}>
          <RoleEditor
            key={edicion === 'nuevo' ? 'nuevo' : edicion.id}
            catalog={catalogo.data}
            role={edicion === 'nuevo' ? null : edicion}
            onDone={() => {
              setEdicion(null)
            }}
          />
        </SectionCard>
      )}

      <SectionCard title="Roles">
        <DataTable
          columns={columnas(setEdicion)}
          data={roles.data?.items ?? []}
          isLoading={roles.isPending}
          emptyMessage="Todavía no hay roles."
          getRowId={(rol) => String(rol.id)}
        />
      </SectionCard>
    </div>
  )
}
