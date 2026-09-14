// Lector de Server-Sent Events sobre `fetch`.
//
// No usa `EventSource`, el lector del navegador, porque no permite mandar la
// cabecera `Authorization`: la alternativa seria poner el token en la URL, y la
// URL queda escrita en los logs del servidor y de cualquier proxy.

export interface StreamEvent {
  readonly type: string
  readonly data: string
}

export class EventStreamError extends Error {
  readonly status: number

  constructor(status: number) {
    super(`El canal de avisos respondio ${String(status)}.`)
    this.name = 'EventStreamError'
    this.status = status
  }
}

interface ReadEventStreamOptions {
  readonly url: string
  readonly token: string
  readonly signal: AbortSignal
  readonly onEvent: (event: StreamEvent) => void
}

function despachar(bloque: string, onEvent: (event: StreamEvent) => void): void {
  let type = 'message'
  const data: string[] = []
  for (const linea of bloque.split('\n')) {
    // Una linea que empieza con ":" es un comentario: el servidor los usa de
    // ping para que un proxy no corte la conexion por inactividad.
    if (linea.startsWith('event:')) {
      type = linea.slice('event:'.length).trim()
    } else if (linea.startsWith('data:')) {
      data.push(linea.slice('data:'.length).trimStart())
    }
  }
  if (data.length > 0) {
    onEvent({ type, data: data.join('\n') })
  }
}

/**
 * Lee el canal hasta que el servidor lo cierra o se aborta la senal.
 *
 * Rechaza con `EventStreamError` si el servidor responde con un error, para
 * que quien llama distinga una credencial vencida de un corte de red.
 */
export async function readEventStream({
  url,
  token,
  signal,
  onEvent,
}: ReadEventStreamOptions): Promise<void> {
  const response = await fetch(url, {
    headers: { Authorization: `Bearer ${token}`, Accept: 'text/event-stream' },
    cache: 'no-store',
    signal,
  })
  if (!response.ok || response.body === null) {
    throw new EventStreamError(response.status)
  }

  const reader = response.body.pipeThrough(new TextDecoderStream()).getReader()
  let pendiente = ''
  let terminado = false
  while (!terminado) {
    const { value, done } = await reader.read()
    terminado = done
    pendiente += (value ?? '').replaceAll('\r\n', '\n')
    let corte = pendiente.indexOf('\n\n')
    while (corte !== -1) {
      despachar(pendiente.slice(0, corte), onEvent)
      pendiente = pendiente.slice(corte + 2)
      corte = pendiente.indexOf('\n\n')
    }
  }
}
