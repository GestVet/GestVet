import type { IconName } from '../../components/icons'
import type { UserRole } from '../../api/types'

export interface NavEntry {
  readonly to: string
  readonly label: string
  readonly icon: IconName
  readonly roles: readonly UserRole[]
}

const TODOS: readonly UserRole[] = [
  'admin',
  'client',
  'veterinarian',
  'emergency_veterinarian',
]
const VETERINARIOS: readonly UserRole[] = ['veterinarian', 'emergency_veterinarian']
const PERSONAL: readonly UserRole[] = ['admin', 'veterinarian', 'emergency_veterinarian']

/**
 * Menu de la aplicacion, en un solo lugar.
 *
 * Cada entrada declara a que roles les aparece, asi que agregar una pantalla
 * es agregar una linea aca y no tocar el armazon. El icono se nombra, no se
 * dibuja: el trazo vive en el registro de iconos.
 */
export const NAV_ENTRIES: readonly NavEntry[] = [
  { to: '/panel', label: 'Panel', icon: 'inicio', roles: TODOS },
  { to: '/mascotas', label: 'Mis mascotas', icon: 'mascota', roles: ['client'] },
  { to: '/reservar', label: 'Reservar cita', icon: 'agenda', roles: ['client'] },
  { to: '/citas', label: 'Citas', icon: 'cita', roles: TODOS },
  { to: '/agenda', label: 'Mi agenda', icon: 'agenda', roles: VETERINARIOS },
  { to: '/clientes', label: 'Clientes', icon: 'cliente', roles: PERSONAL },
  {
    to: '/emergencia-cliente-nuevo',
    label: 'Emergencia (cliente nuevo)',
    icon: 'emergencia',
    roles: PERSONAL,
  },
  { to: '/personal', label: 'Personal', icon: 'personal', roles: ['admin'] },
  { to: '/pagos', label: 'Pagos', icon: 'pago', roles: ['admin'] },
  { to: '/reclamos', label: 'Reclamos', icon: 'alerta', roles: ['admin'] },
  { to: '/indicadores', label: 'Indicadores', icon: 'indicadores', roles: ['admin'] },
  { to: '/movimientos', label: 'Movimientos', icon: 'buscar', roles: ['admin'] },
]

export function entriesForRole(role: UserRole): readonly NavEntry[] {
  return NAV_ENTRIES.filter((entry) => entry.roles.includes(role))
}
