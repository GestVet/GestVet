import { Link } from 'react-router'

import type { UserRole } from '../../api/types'
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
}

// El panel de cada rol, como en el original: una rejilla de accesos. Lo que
// cambia es que aca vive en una tabla y no en cuatro paginas HTML distintas.
const ACCESOS: Record<UserRole, readonly Acceso[]> = {
  client: [
    {
      to: '/mascotas',
      icon: 'mascota',
      title: 'Mis mascotas',
      description: 'Registralas y dalas de baja cuando corresponda.',
    },
    {
      to: '/reservar',
      icon: 'agenda',
      title: 'Reservar cita',
      description: 'Elegí veterinario, motivo y una hora que esté libre.',
    },
    {
      to: '/citas',
      icon: 'cita',
      title: 'Mis citas',
      description: 'Mirá el estado de cada una y cancelá si no vas a poder.',
    },
  ],
  veterinarian: [
    {
      to: '/agenda',
      icon: 'agenda',
      title: 'Mi agenda',
      description: 'Publicá los tramos en los que atendés.',
    },
    {
      to: '/citas',
      icon: 'cita',
      title: 'Mis citas',
      description: 'Confirmá, completá o cancelá lo que tenés asignado.',
    },
    {
      to: '/clientes',
      icon: 'cliente',
      title: 'Clientes',
      description: 'Consultá el padrón de la clínica.',
    },
  ],
  emergency_veterinarian: [
    {
      to: '/agenda',
      icon: 'agenda',
      title: 'Mi guardia',
      description: 'Publicá los tramos en los que estás de guardia.',
    },
    {
      to: '/citas',
      icon: 'emergencia',
      title: 'Emergencias',
      description: 'Las que el sistema te asignó automáticamente.',
    },
    {
      to: '/clientes',
      icon: 'cliente',
      title: 'Clientes',
      description: 'Consultá el padrón de la clínica.',
    },
  ],
  admin: [
    {
      to: '/personal',
      icon: 'personal',
      title: 'Personal',
      description: 'Dar de alta veterinarios y asignar el turno de guardia.',
    },
    {
      to: '/clientes',
      icon: 'cliente',
      title: 'Clientes',
      description: 'Padrón completo y activación de cuentas.',
    },
    {
      to: '/citas',
      icon: 'cita',
      title: 'Citas',
      description: 'Todas las citas de la clínica.',
    },
    {
      to: '/movimientos',
      icon: 'buscar',
      title: 'Movimientos',
      description: 'Qué hizo cada cuenta y cuándo, la administración incluida.',
    },
  ],
}

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
          {ACCESOS[user.role].map((acceso) => (
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
