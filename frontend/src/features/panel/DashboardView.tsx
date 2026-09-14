import { Link } from 'react-router'

import type { PermissionCode } from '../../api/types'
import Icon from '../../components/Icon'
import type { IconName } from '../../components/icons'
import PageHeader from '../../components/PageHeader'
import { Button } from '../../components/ui/button'
import { useSession } from '../../store/session'

interface Acceso {
  readonly to: string
  readonly icon: IconName
  readonly title: string
  readonly description: string
  readonly permission: PermissionCode
}

// Los accesos del panel, como en el original: una rejilla. Cada uno declara el
// permiso que lo muestra, igual que el menú, así que un rol editado cambia el
// panel sin tocar código.
const ACCESOS: readonly Acceso[] = [
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

export default function DashboardView() {
  const user = useSession((state) => state.user)

  if (user === null) {
    return null
  }

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title={`Hola, ${user.first_name}`}
        description={user.email}
        actions={
          <Button asChild variant="outline" size="lg" className="h-10 px-4">
            <Link to="/perfil">
              <Icon name="perfil" size={16} />
              <span>Editar perfil</span>
            </Link>
          </Button>
        }
      />

      <nav aria-label="Accesos del panel">
        <ul className="m-0 grid list-none gap-4 p-0 sm:grid-cols-2 lg:grid-cols-3">
          {ACCESOS.filter((acceso) => user.permissions.includes(acceso.permission)).map((acceso) => (
            <li key={acceso.to}>
              <Link
                to={acceso.to}
                className="flex h-full flex-col gap-2 rounded-xl bg-card p-5 text-card-foreground shadow-sm ring-1 ring-foreground/10 transition-shadow outline-none hover:shadow-md focus-visible:ring-3 focus-visible:ring-ring/50"
              >
                <Icon className="text-primary" name={acceso.icon} size={28} />
                <h2 className="m-0 font-heading text-lg font-semibold text-primary">
                  {acceso.title}
                </h2>
                <p className="m-0 text-sm leading-relaxed text-muted-foreground">
                  {acceso.description}
                </p>
              </Link>
            </li>
          ))}
        </ul>
      </nav>
    </div>
  )
}
