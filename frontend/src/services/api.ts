import axios from 'axios'

const DEFAULT_BASE_URL = '/api/v1'

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

/** Mensaje legible de un error del API, con respaldo si no trae detalle. */
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
