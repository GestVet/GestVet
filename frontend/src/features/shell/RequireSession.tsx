import { Navigate, Outlet, useLocation } from 'react-router'

import type { PermissionCode } from '../../api/types'
import { hasPermission, useSession } from '../../store/session'

interface RequireSessionProps {
  /** Permiso que exige la ruta. Sin el, basta con estar autenticado. */
  readonly permission?: PermissionCode
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
  if (permission !== undefined && !hasPermission(user, permission)) {
    return <Navigate to="/panel" replace />
  }
  return <Outlet />
}
