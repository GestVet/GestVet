import { Navigate, Outlet, useLocation } from 'react-router'

import type { PermissionCode } from '../../api/types'
import { hasPermission, useSession } from '../../store/session'

interface RequireSessionProps {
  /**
   * Permiso que exige la ruta, o una lista: con lista alcanza con tener
   * cualquiera de ellos (una pantalla con secciones para audiencias
   * distintas). Sin nada, basta con estar autenticado.
   */
  readonly permission?: PermissionCode | readonly PermissionCode[]
}

function tienePermiso(
  user: Parameters<typeof hasPermission>[0],
  permission: PermissionCode | readonly PermissionCode[],
): boolean {
  const permisos = typeof permission === 'string' ? [permission] : permission
  return permisos.some((uno) => hasPermission(user, uno))
}

/**
 * Guarda de rutas.
 *
 * Es una comodidad de la interfaz, no una medida de seguridad: quien llegue
 * igual a la pantalla se encuentra con que el API le responde 401 o 403. La
 * autorizacion de verdad vive en el servidor. Si le quitan el permiso con la
 * pantalla abierta, el aviso en tiempo real actualiza la sesion y esta guarda
 * lo devuelve al panel.
 */
export default function RequireSession({ permission }: RequireSessionProps) {
  const user = useSession((state) => state.user)
  const location = useLocation()

  if (user === null) {
    return <Navigate to="/acceso" replace state={{ from: location.pathname }} />
  }
  if (permission !== undefined && !tienePermiso(user, permission)) {
    return <Navigate to="/panel" replace />
  }
  return <Outlet />
}
