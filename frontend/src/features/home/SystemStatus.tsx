import type { HealthResponse } from '../../api/types'

type ConnectionState = 'checking' | 'online' | 'offline'

const CONNECTION_LABELS: Record<ConnectionState, string> = {
  checking: 'Comprobando conexión…',
  online: 'API conectada',
  offline: 'API no disponible',
}

// El punto acompana a la etiqueta, no la reemplaza: el estado se lee igual
// sin distinguir el color.
const DOT_CLASSES: Record<ConnectionState, string> = {
  checking: 'bg-muted-foreground',
  online: 'bg-success',
  offline: 'bg-destructive',
}

interface SystemStatusProps {
  readonly isPending: boolean
  readonly isError: boolean
  readonly data?: HealthResponse
}

function resolveConnectionState(isPending: boolean, isOnline: boolean): ConnectionState {
  if (isPending) {
    return 'checking'
  }
  return isOnline ? 'online' : 'offline'
}

export default function SystemStatus({ isPending, isError, data }: SystemStatusProps) {
  const connection = resolveConnectionState(isPending, data?.status === 'ok')
  const detail = data
    ? `${data.service} · v${data.version}`
    : 'No se pudo contactar con el backend.'
  const showDetail = data !== undefined || isError

  return (
    <aside aria-live="polite" className="flex flex-col gap-2 rounded-xl bg-muted p-4">
      <h2 className="m-0 font-heading text-base font-semibold text-foreground">
        Estado del sistema
      </h2>
      <p className="m-0 flex items-center gap-2 text-sm font-medium">
        <span aria-hidden="true" className={`size-2.5 rounded-full ${DOT_CLASSES[connection]}`} />
        {CONNECTION_LABELS[connection]}
      </p>
      {showDetail ? <p className="m-0 text-xs text-muted-foreground">{detail}</p> : null}
    </aside>
  )
}
