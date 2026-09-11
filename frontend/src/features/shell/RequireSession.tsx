import { Navigate, Outlet, useLocation } from 'react-router'

import type { UserRole } from '../../api/types'
import { useSession } from '../../store/session'

interface RequireSessionProps {
  /** Roles admitidos. Sin la lista, basta con estar autenticado. */
  readonly roles?: readonly UserRole[]
}

/**
 * Guarda de rutas.
 *
 * Es una comodidad de la interfaz, no una medida de seguridad: quien llegue
 * igual a la pantalla se encuentra con que el API le responde 401 o 403. La
 * autorizacion de verdad vive en el servidor.
 */
export default function RequireSession({ roles }: RequireSessionProps) {
  const user = useSession((state) => state.user)
  const location = useLocation()

  if (user === null) {
    return <Navigate to="/acceso" replace state={{ from: location.pathname }} />
  }
  if (roles !== undefined && !roles.includes(user.role)) {
    return <Navigate to="/panel" replace />
  }
  return <Outlet />
}
