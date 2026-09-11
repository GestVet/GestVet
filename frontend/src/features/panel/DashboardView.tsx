import { Link } from 'react-router'

import Icon from '../../components/Icon'
import type { IconName } from '../../components/icons'
import type { UserRole } from '../../api/types'
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
    <div className="stack">
      <div className="page-header">
        <div>
          <span className="eyebrow">{user.role}</span>
          <h1>Hola, {user.first_name}</h1>
          <p className="muted">{user.email}</p>
        </div>
        <Link className="btn btn-plain" to="/perfil">
          <Icon name="perfil" size={16} />
          <span>Editar perfil</span>
        </Link>
      </div>

      <section className="card-grid">
        {ACCESOS[user.role].map((acceso) => (
          <Link className="tile" key={acceso.to} to={acceso.to}>
            <Icon className="tile-icon" name={acceso.icon} size={28} />
            <h3>{acceso.title}</h3>
            <p>{acceso.description}</p>
          </Link>
        ))}
      </section>
    </div>
  )
}
