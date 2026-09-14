import { api } from '../services/api'
import type {
  AccessRoleListResponse,
  AccessRoleResponse,
  CreateAccessRoleRequest,
  PermissionCatalogResponse,
  RoleAssignmentListResponse,
  UpdateAccessRoleRequest,
} from './types'

export const accessQueryKey = ['access'] as const
export const permissionCatalogQueryKey = [...accessQueryKey, 'permissions'] as const
export const accessRolesQueryKey = [...accessQueryKey, 'roles'] as const
export const roleAssignmentsQueryKey = [...accessQueryKey, 'assignments'] as const

export async function fetchPermissionCatalog(): Promise<PermissionCatalogResponse> {
  const { data } = await api.get<PermissionCatalogResponse>('/access/permissions')
  return data
}

export async function fetchAccessRoles(): Promise<AccessRoleListResponse> {
  const { data } = await api.get<AccessRoleListResponse>('/access/roles')
  return data
}

export async function fetchRoleAssignments(): Promise<RoleAssignmentListResponse> {
  const { data } = await api.get<RoleAssignmentListResponse>('/access/assignments')
  return data
}

export async function createAccessRole(
  payload: CreateAccessRoleRequest,
): Promise<AccessRoleResponse> {
  const { data } = await api.post<AccessRoleResponse>('/access/roles', payload)
  return data
}

export async function updateAccessRole(
  roleId: number,
  payload: UpdateAccessRoleRequest,
): Promise<AccessRoleResponse> {
  const { data } = await api.patch<AccessRoleResponse>(`/access/roles/${String(roleId)}`, payload)
  return data
}

export async function deleteAccessRole(roleId: number): Promise<void> {
  await api.delete(`/access/roles/${String(roleId)}`)
}

/** Sin rol, la cuenta vuelve al rol de sistema de su tipo. */
export async function assignAccessRole(userId: number, roleId: number | null): Promise<void> {
  await api.put(`/access/users/${String(userId)}/role`, { role_id: roleId })
}
