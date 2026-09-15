import type { IconName } from '../../components/icons'
import type { PermissionCode } from '../../api/types'

export interface NavEntry {
  readonly to: string
  readonly label: string
  readonly icon: IconName
  /** Permiso que la muestra. Sin permiso, la ve toda cuenta. */
  readonly permission?: PermissionCode
}

/**
 * Menu de la aplicacion, en un solo lugar.
 *
 * Cada entrada declara el permiso que la muestra, asi que agregar una pantalla
 * es agregar una linea aca y un rol editado cambia el menu sin tocar codigo.
 * El permiso es el mismo que exige la ruta. El icono se nombra, no se dibuja.
 */
export const NAV_ENTRIES: readonly NavEntry[] = [
  { to: '/panel', label: 'Panel', icon: 'inicio' },
  { to: '/mascotas', label: 'Mis mascotas', icon: 'mascota', permission: 'pets.manage_own' },
  { to: '/reservar', label: 'Reservar cita', icon: 'agenda', permission: 'appointments.book' },
  { to: '/citas', label: 'Citas', icon: 'cita', permission: 'appointments.read' },
  { to: '/agenda', label: 'Mis turnos', icon: 'agenda', permission: 'schedule.read_own' },
  { to: '/clientes', label: 'Clientes', icon: 'cliente', permission: 'clients.read' },
  {
    to: '/emergencia-cliente-nuevo',
    label: 'Emergencia (cliente nuevo)',
    icon: 'emergencia',
    permission: 'emergencies.open_walk_in',
  },
  { to: '/personal', label: 'Personal', icon: 'personal', permission: 'staff.read' },
  { to: '/turnos', label: 'Turnos y guardias', icon: 'horario', permission: 'schedule.manage' },
  {
    to: '/especies-y-razas',
    label: 'Especies y razas',
    icon: 'raza',
    permission: 'pets.manage_catalog',
  },
  { to: '/roles', label: 'Roles y permisos', icon: 'permisos', permission: 'roles.manage' },
  { to: '/pagos', label: 'Pagos', icon: 'pago', permission: 'payments.report' },
  { to: '/reclamos', label: 'Reclamos', icon: 'alerta', permission: 'complaints.read' },
  { to: '/indicadores', label: 'Indicadores', icon: 'indicadores', permission: 'insights.read' },
  {
    to: '/panorama-mascotas',
    label: 'Panorama de mascotas',
    icon: 'mascota',
    permission: 'pets.overview_read',
  },
  { to: '/movimientos', label: 'Movimientos', icon: 'buscar', permission: 'activity.read' },
]

export function entriesFor(permissions: readonly PermissionCode[]): readonly NavEntry[] {
  return NAV_ENTRIES.filter(
    (entry) => entry.permission === undefined || permissions.includes(entry.permission),
  )
}
