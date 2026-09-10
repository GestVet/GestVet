import { useQuery } from '@tanstack/react-query'

import { fetchHealth, healthQueryKey } from '../../api/health'

type ConnectionState = 'checking' | 'online' | 'offline'

const CONNECTION_LABELS: Record<ConnectionState, string> = {
  checking: 'Comprobando conexión…',
  online: 'API conectada',
  offline: 'API no disponible',
}

const MODULES = [
  {
    title: 'Operación',
    description: 'Usuarios, mascotas, horarios y citas con reglas de propiedad y asignación.',
  },
  {
    title: 'Analítica',
    description: 'Indicadores para decidir sobre demanda, estados y carga veterinaria.',
  },
  {
    title: 'Inteligencia',
    description: 'Funciones de IA controladas, explicables y separadas del núcleo.',
  },
]

function resolveConnectionState(isPending: boolean, isOnline: boolean): ConnectionState {
  if (isPending) {
    return 'checking'
  }
  return isOnline ? 'online' : 'offline'
}

export default function HomeView() {
  const health = useQuery({
    queryKey: healthQueryKey,
    queryFn: fetchHealth,
  })

  const isOnline = health.data?.status === 'ok'
  const connection = resolveConnectionState(health.isPending, isOnline)
  const detail = health.data
    ? `${health.data.service} · v${health.data.version}`
    : 'No se pudo contactar con el backend.'
  const showDetail = health.data !== undefined || health.isError

  return (
    <>
      <section className="hero">
        <div>
          <span className="eyebrow">Sistema integral de gestión veterinaria</span>
          <h1>Una base sólida para cuidar mejor.</h1>
          <p className="hero-copy">
            GestVet centralizará clientes, mascotas, disponibilidad, citas, analítica e inteligencia
            asistida en una experiencia clara y responsive.
          </p>
        </div>

        <aside className="status-card" aria-live="polite">
          <h2>Estado del backend</h2>
          <div className="status">
            <span className={isOnline ? 'status-dot is-online' : 'status-dot'} />
            <strong>{CONNECTION_LABELS[connection]}</strong>
          </div>
          {showDetail ? <p className="status-detail">{detail}</p> : null}
        </aside>
      </section>

      <section className="features" aria-label="Módulos base">
        {MODULES.map((module) => (
          <article className="feature-card" key={module.title}>
            <h2>{module.title}</h2>
            <p>{module.description}</p>
          </article>
        ))}
      </section>
    </>
  )
}
