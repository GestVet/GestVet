import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router'

import { fetchHealth, healthQueryKey } from '../../api/health'
import Icon from '../../components/Icon'
import type { IconName } from '../../components/icons'

type ConnectionState = 'checking' | 'online' | 'offline'

const CONNECTION_LABELS: Record<ConnectionState, string> = {
  checking: 'Comprobando conexión…',
  online: 'API conectada',
  offline: 'API no disponible',
}

interface Modulo {
  readonly icon: IconName
  readonly title: string
  readonly description: string
}

const MODULOS: readonly Modulo[] = [
  {
    icon: 'mascota',
    title: 'Tus mascotas',
    description: 'Registrá a cada una con su especie, su raza y su fecha de nacimiento.',
  },
  {
    icon: 'agenda',
    title: 'Citas con hora real',
    description: 'La agenda muestra solo lo que el veterinario publicó y todavía está libre.',
  },
  {
    icon: 'emergencia',
    title: 'Emergencias 24 horas',
    description: 'Se abre en el momento y el sistema asigna al veterinario de guardia.',
  },
]

function resolveConnectionState(isPending: boolean, isOnline: boolean): ConnectionState {
  if (isPending) {
    return 'checking'
  }
  return isOnline ? 'online' : 'offline'
}

export default function HomeView() {
  const health = useQuery({ queryKey: healthQueryKey, queryFn: fetchHealth })

  const isOnline = health.data?.status === 'ok'
  const connection = resolveConnectionState(health.isPending, isOnline)
  const detail = health.data
    ? `${health.data.service} · v${health.data.version}`
    : 'No se pudo contactar con el backend.'
  const showDetail = health.data !== undefined || health.isError

  return (
    <div className="stack">
      <section className="hero card">
        <div>
          <span className="eyebrow">Clínica veterinaria en Trujillo</span>
          <h1>Bienvenido a GestVet</h1>
          <p className="hero-copy">
            Como clínica líder en la ciudad, ampliamos nuestros servicios para darte la
            seguridad y el cuidado que tu mascota merece. Atendemos las 24 horas del día.
          </p>
          <div className="inline">
            <Link className="btn btn-green" to="/registro">
              <Icon name="agregar" size={16} />
              <span>Crear una cuenta</span>
            </Link>
            <Link className="btn btn-blue" to="/acceso">
              <span>Ya tengo cuenta</span>
            </Link>
          </div>
        </div>

        <aside className="card" aria-live="polite">
          <h2>Estado del sistema</h2>
          <div className="status">
            <span className={isOnline ? 'status-dot is-online' : 'status-dot'} />
            <strong>{CONNECTION_LABELS[connection]}</strong>
          </div>
          {showDetail ? <p className="status-detail">{detail}</p> : null}
        </aside>
      </section>

      <section className="card-grid" aria-label="Qué ofrece el sistema">
        {MODULOS.map((modulo) => (
          <article className="tile" key={modulo.title}>
            <Icon className="tile-icon" name={modulo.icon} size={28} />
            <h3>{modulo.title}</h3>
            <p>{modulo.description}</p>
          </article>
        ))}
      </section>
    </div>
  )
}
