import axios, { type InternalAxiosRequestConfig } from 'axios'

import { logger } from './logger'

const DEFAULT_BASE_URL = '/api/v1'

// El mismo nombre que usa el backend. El identificador lo genera el navegador
// y el servidor lo respeta, asi un error de la consola y su linea en los logs
// del servidor se encuentran buscando el mismo valor.
export const REQUEST_ID_HEADER = 'X-Request-ID'

const SERVER_ERROR = 500
const CLIENT_ERROR = 400
const UNAUTHORIZED = 401

// Lo registra el almacen de sesion: los servicios son la capa mas baja y no
// pueden importarlo.
const sesion: { alVencer: (() => void) | null } = { alVencer: null }

/** Qué hacer cuando el servidor rechaza la credencial de una petición. */
export function setUnauthorizedHandler(handler: (() => void) | null): void {
  sesion.alVencer = handler
}

/**
 * Si vale la pena repetir una consulta que falló.
 *
 * Un 4xx no cambia por repetir la petición: un 401 de una sesión vencida
 * reintentado solo demora el aviso. Un corte de red o un 5xx, quizá sí.
 */
export function debeReintentar(fallos: number, error: unknown): boolean {
  const estado = axios.isAxiosError(error) ? error.response?.status : undefined
  if (estado !== undefined && estado >= CLIENT_ERROR && estado < SERVER_ERROR) {
    return false
  }
  return fallos < 1
}

// `import.meta.env` llega sin tipar salvo por los tipos de Vite, asi que se
// acota aca y no en cada llamada.
const configuredBaseUrl: string | undefined = import.meta.env.VITE_API_BASE_URL

export const api = axios.create({
  baseURL: configuredBaseUrl ?? DEFAULT_BASE_URL,
  headers: {
    Accept: 'application/json',
    'Content-Type': 'application/json',
  },
})

const httpLogger = logger.child({ module: 'http' })

// Cuando empezo cada peticion, para anotar su duracion. Un WeakMap no retiene
// la configuracion de una peticion que ya termino.
const inicios = new WeakMap<InternalAxiosRequestConfig, number>()

/**
 * Un identificador de peticion.
 *
 * `crypto.randomUUID` solo existe en un contexto seguro (HTTPS o localhost).
 * Servida por HTTP en otra direccion, la aplicacion no puede dejar de hacer
 * peticiones por eso, asi que arma uno con `getRandomValues`.
 */
function nuevoIdDePeticion(): string {
  if (typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID()
  }
  const bytes = crypto.getRandomValues(new Uint8Array(16))
  return Array.from(bytes, (byte) => byte.toString(16).padStart(2, '0')).join('')
}

function duracionMs(config: InternalAxiosRequestConfig | undefined): number | undefined {
  const inicio = config === undefined ? undefined : inicios.get(config)
  return inicio === undefined ? undefined : Math.round(performance.now() - inicio)
}

function registrarFallo(error: unknown): void {
  if (!axios.isAxiosError(error)) {
    httpLogger.error({ err: error }, 'http.request_failed')
    return
  }
  const { config, response } = error
  const datos = {
    method: config?.method,
    url: config?.url,
    status: response?.status,
    code: error.code,
    requestId: config?.headers.get(REQUEST_ID_HEADER),
    durationMs: duracionMs(config),
  }
  // Sin respuesta es un corte de red o un servidor caido. Un 4xx es la
  // respuesta esperada a un dato invalido: se anota como aviso, no como error.
  if (response === undefined || response.status >= SERVER_ERROR) {
    httpLogger.error(datos, 'http.request_failed')
    return
  }
  httpLogger.warn(datos, 'http.request_rejected')
}

api.interceptors.request.use((config) => {
  config.headers.set(REQUEST_ID_HEADER, nuevoIdDePeticion())
  inicios.set(config, performance.now())
  return config
})

api.interceptors.response.use(
  (response) => {
    httpLogger.debug(
      {
        method: response.config.method,
        url: response.config.url,
        status: response.status,
        durationMs: duracionMs(response.config),
      },
      'http.request_completed',
    )
    return response
  },
  (error: unknown) => {
    registrarFallo(error)
    // Un 401 de una petición que llevaba credencial es una sesión vencida o
    // revocada. Seguir mostrando pantallas vacías confunde: se cierra la sesión
    // y el acceso explica qué pasó. Un 401 sin credencial, como una contraseña
    // equivocada al entrar, lo resuelve su propio formulario.
    if (
      axios.isAxiosError(error) &&
      error.response?.status === UNAUTHORIZED &&
      error.config?.headers.has('Authorization') === true
    ) {
      sesion.alVencer?.()
    }
    throw error
  },
)

/**
 * Pone o quita la credencial que acompana a cada peticion.
 *
 * La llama el almacen de sesion, nunca al reves: los servicios son la capa mas
 * baja y no pueden conocer el estado de cliente. Asi el token vive en un solo
 * lugar y ninguna pantalla tiene que acordarse de adjuntarlo.
 */
export function setAuthToken(token: string | null): void {
  if (token === null) {
    delete api.defaults.headers.common.Authorization
    return
  }
  api.defaults.headers.common.Authorization = `Bearer ${token}`
}

/**
 * Forma del cuerpo de error que devuelve FastAPI.
 *
 * `detail` es un texto cuando lo levanta el proyecto y una lista de problemas
 * por campo cuando lo levanta la validacion de Pydantic.
 */
interface ApiErrorBody {
  detail?: string | { msg?: string }[]
}

export function errorMessage(error: unknown, fallback: string): string {
  if (!axios.isAxiosError<ApiErrorBody>(error)) {
    return fallback
  }

  const detail = error.response?.data.detail
  if (typeof detail === 'string') {
    return detail
  }
  return detail?.[0]?.msg ?? fallback
}

/** El código HTTP de un error del servidor, o `undefined` si ni siquiera llegó a responder. */
export function errorStatus(error: unknown): number | undefined {
  return axios.isAxiosError(error) ? error.response?.status : undefined
}
