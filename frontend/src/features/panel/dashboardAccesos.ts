import type { DashboardBlockPreference } from '../../api/layout'
import type { PermissionCode } from '../../api/types'
import type { IconName } from '../../components/icons'

export interface Acceso {
  readonly to: string
  readonly icon: IconName
  readonly title: string
  readonly description: string
  readonly permission: PermissionCode
}

export interface DashboardBlockView {
  readonly id: string
  readonly visible: boolean
  readonly acceso: Acceso
}

// Los accesos del panel, como en el original: una rejilla. Cada uno declara el
// permiso que lo muestra, igual que el menú, así que un rol editado cambia el
// panel sin tocar código.
export const ACCESOS: readonly Acceso[] = [
  {
    to: '/mascotas',
    icon: 'mascota',
    title: 'Mis mascotas',
    description: 'Regístralas y dalas de baja cuando corresponda.',
    permission: 'pets.manage_own',
  },
  {
    to: '/reservar',
    icon: 'agenda',
    title: 'Reservar cita',
    description: 'Elige el día, el veterinario y una hora libre.',
    permission: 'appointments.book',
  },
  {
    to: '/agenda',
    icon: 'agenda',
    title: 'Mis turnos',
    description: 'Tus turnos y guardias de la semana.',
    permission: 'schedule.read_own',
  },
  {
    to: '/citas',
    icon: 'cita',
    title: 'Citas',
    description: 'El estado de cada una y lo que falta hacer.',
    permission: 'appointments.read',
  },
  {
    to: '/clientes',
    icon: 'cliente',
    title: 'Clientes',
    description: 'El padrón de la clínica y sus mascotas.',
    permission: 'clients.read',
  },
  {
    to: '/personal',
    icon: 'personal',
    title: 'Personal',
    description: 'Dar de alta veterinarios y asignarles un rol.',
    permission: 'staff.read',
  },
  {
    to: '/turnos',
    icon: 'horario',
    title: 'Turnos y guardias',
    description: 'Quién atiende y quién está de guardia cada día.',
    permission: 'schedule.manage',
  },
  {
    to: '/roles',
    icon: 'permisos',
    title: 'Roles y permisos',
    description: 'Qué puede hacer cada cuenta.',
    permission: 'roles.manage',
  },
  {
    to: '/movimientos',
    icon: 'buscar',
    title: 'Movimientos',
    description: 'Qué hizo cada cuenta y cuándo, la administración incluida.',
    permission: 'activity.read',
  },
]

/**
 * Cruza lo guardado con lo que la cuenta puede ver hoy.
 *
 * Los ids desconocidos o sin permiso se descartan y las tarjetas nuevas se
 * agregan al final, visibles: asi una pantalla que se suma despues aparece
 * aunque nadie haya vuelto a personalizar. Sin preferencia guardada, el orden
 * es el de `ACCESOS` y todas se ven.
 */
export function resolveDashboardBlocks(
  saved: readonly DashboardBlockPreference[],
  permissions: readonly PermissionCode[],
): readonly DashboardBlockView[] {
  const disponibles = ACCESOS.filter((acceso) => permissions.includes(acceso.permission))
  const porRuta = new Map(disponibles.map((acceso) => [acceso.to, acceso]))
  const vistas = new Set<string>()
  const bloques: DashboardBlockView[] = []

  for (const guardado of saved) {
    const acceso = porRuta.get(guardado.id)
    if (acceso === undefined || vistas.has(guardado.id)) {
      continue
    }
    vistas.add(guardado.id)
    bloques.push({ id: guardado.id, visible: guardado.visible, acceso })
  }

  for (const acceso of disponibles) {
    if (!vistas.has(acceso.to)) {
      bloques.push({ id: acceso.to, visible: true, acceso })
    }
  }

  return bloques
}

/** Deja las tarjetas en el orden de rutas indicado, sin perder ninguna. */
export function reorderDashboardBlocks(
  blocks: readonly DashboardBlockView[],
  ids: readonly string[],
): readonly DashboardBlockView[] {
  const porId = new Map(blocks.map((block) => [block.id, block]))
  const ordenados = ids.flatMap((id) => {
    const block = porId.get(id)
    return block === undefined ? [] : [block]
  })
  const vistas = new Set(ordenados.map((block) => block.id))
  const resto = blocks.filter((block) => !vistas.has(block.id))
  return [...ordenados, ...resto]
}

/** Muestra u oculta una tarjeta conservando su lugar en la rejilla. */
export function toggleDashboardBlock(
  blocks: readonly DashboardBlockView[],
  id: string,
): readonly DashboardBlockView[] {
  return blocks.map((block) =>
    block.id === id ? { ...block, visible: !block.visible } : block,
  )
}
