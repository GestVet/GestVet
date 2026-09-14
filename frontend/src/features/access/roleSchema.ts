import { z } from 'zod'

import type {
  AccessRoleResponse,
  PermissionCatalogResponse,
  PermissionCode,
  UserRole,
} from '../../api/types'

// Los mismos límites que aplica el servidor al nombre y la descripción.
const MIN_NOMBRE = 3
const MAX_NOMBRE = 60
const MAX_DESCRIPCION = 200

export const TIPOS_DE_CUENTA = ['admin', 'veterinarian', 'client'] as const

export const ETIQUETA_DE_TIPO: Record<UserRole, string> = {
  admin: 'Administración',
  client: 'Cliente',
  veterinarian: 'Veterinario',
}

export const roleSchema = z.object({
  name: z
    .string()
    .trim()
    .min(MIN_NOMBRE, `Escribe al menos ${String(MIN_NOMBRE)} caracteres.`)
    .max(MAX_NOMBRE, `Usa hasta ${String(MAX_NOMBRE)} caracteres.`),
  description: z
    .string()
    .trim()
    .max(MAX_DESCRIPCION, `Usa hasta ${String(MAX_DESCRIPCION)} caracteres.`),
  account_kind: z.enum(TIPOS_DE_CUENTA),
  permissions: z.array(z.custom<PermissionCode>()),
})

export type RoleFormValues = z.infer<typeof roleSchema>

export function roleFormValues(role: AccessRoleResponse | null): RoleFormValues {
  if (role === null) {
    return { name: '', description: '', account_kind: 'veterinarian', permissions: [] }
  }
  return {
    name: role.name,
    description: role.description,
    account_kind: role.account_kind,
    permissions: role.permissions,
  }
}

/** Los permisos que un tipo de cuenta puede tener, según el catálogo del servidor. */
export function permissionsForKind(
  catalog: PermissionCatalogResponse,
  kind: UserRole,
): ReadonlySet<PermissionCode> {
  return new Set(
    catalog.items.filter((item) => item.account_kinds.includes(kind)).map((item) => item.code),
  )
}
