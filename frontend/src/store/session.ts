import { create } from 'zustand'

import { setAuthToken, setUnauthorizedHandler } from '../services/api'
import { logger } from '../services/logger'
import { queryClient } from '../services/queryClient'
import type {
  AccessTokenResponse,
  CurrentUserResponse,
  PermissionCode,
  UserResponse,
} from '../api/types'

// La version va en la clave: una sesion guardada antes de existir los permisos
// no los trae, y leerla como si los tuviera dejaria la interfaz sin menu.
const STORAGE_KEY = 'gestvet.session.v2'
const MS_POR_SEGUNDO = 1000

interface StoredSession {
  token: string
  user: CurrentUserResponse
}

interface SessionState {
  token: string | null
  user: CurrentUserResponse | null
  /** La sesion se cerro sola porque el token vencio: el acceso lo explica. */
  expired: boolean
  signIn: (response: AccessTokenResponse) => void
  /** Aplica un perfil nuevo. Si la respuesta no trae permisos, se conservan los que habia. */
  updateUser: (user: UserResponse | CurrentUserResponse) => void
  signOut: () => void
  /** Cierra la sesion porque el servidor ya no acepta el token. */
  expire: () => void
}

/**
 * Lee la sesion guardada del navegador.
 *
 * El token vive en `localStorage` para que recargar la pagina no eche al
 * usuario. Cualquier lectura puede fallar en una ventana privada o con el
 * almacenamiento bloqueado, asi que el fallo se trata como "no hay sesion".
 */
function readStoredSession(): StoredSession | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw === null ? null : (JSON.parse(raw) as StoredSession)
  } catch {
    return null
  }
}

function writeStoredSession(session: StoredSession | null): void {
  try {
    if (session === null) {
      localStorage.removeItem(STORAGE_KEY)
      return
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(session))
  } catch {
    // Sin almacenamiento la sesion dura lo que dure la pestana. Es una
    // degradacion aceptable; perder el acceso por no poder escribir no lo es.
  }
}

/**
 * Cuando vence el token, en milisegundos, o `null` si no se puede leer.
 *
 * Solo se lee la fecha de vencimiento para no mostrar pantallas que igual van a
 * responder 401. La firma la comprueba el servidor, que es quien decide.
 */
function venceEn(token: string): number | null {
  try {
    const carga = token.split('.')[1] ?? ''
    const datos = JSON.parse(atob(carga.replaceAll('-', '+').replaceAll('_', '/'))) as {
      exp?: unknown
    }
    return typeof datos.exp === 'number' ? datos.exp * MS_POR_SEGUNDO : null
  } catch {
    return null
  }
}

function estaVencido(token: string): boolean {
  const vencimiento = venceEn(token)
  return vencimiento !== null && vencimiento <= Date.now()
}

const temporizador: { id: ReturnType<typeof setTimeout> | undefined } = { id: undefined }

// Cierra la sesion en el momento en que vence, en vez de esperar a que una
// pantalla se quede sin datos por un 401.
function programarVencimiento(token: string | null): void {
  clearTimeout(temporizador.id)
  const vencimiento = token === null ? null : venceEn(token)
  if (vencimiento === null) {
    return
  }
  temporizador.id = setTimeout(
    () => {
      useSession.getState().expire()
    },
    Math.max(vencimiento - Date.now(), 0),
  )
}

function limpiarSesion(): void {
  setAuthToken(null)
  writeStoredSession(null)
  programarVencimiento(null)
  // Nada de la cuenta anterior queda en el cache para la siguiente.
  queryClient.clear()
}

const guardada = readStoredSession()
const restored = guardada !== null && !estaVencido(guardada.token) ? guardada : null
if (guardada !== null && restored === null) {
  writeStoredSession(null)
}
setAuthToken(restored?.token ?? null)

export const useSession = create<SessionState>((set, get) => ({
  token: restored?.token ?? null,
  user: restored?.user ?? null,
  expired: guardada !== null && restored === null,

  signIn: (response) => {
    setAuthToken(response.access_token)
    writeStoredSession({ token: response.access_token, user: response.user })
    set({ token: response.access_token, user: response.user, expired: false })
    programarVencimiento(response.access_token)
    logger.info({ userId: response.user.id, role: response.user.role }, 'auth.signed_in')
  },

  updateUser: (user) => {
    set((state) => {
      if (state.token === null || state.user === null) {
        return {}
      }
      const merged: CurrentUserResponse = { ...state.user, ...user }
      writeStoredSession({ token: state.token, user: merged })
      return { user: merged }
    })
  },

  signOut: () => {
    limpiarSesion()
    set({ token: null, user: null, expired: false })
    logger.info('auth.signed_out')
  },

  expire: () => {
    if (get().token === null) {
      return
    }
    limpiarSesion()
    set({ token: null, user: null, expired: true })
    logger.warn('auth.session_expired')
  },
}))

programarVencimiento(restored?.token ?? null)
setUnauthorizedHandler(() => {
  useSession.getState().expire()
})

export function hasPermission(
  user: CurrentUserResponse | null,
  permission: PermissionCode,
): boolean {
  return user?.permissions.includes(permission) ?? false
}

/**
 * Si la cuenta puede hacer algo, segun los permisos de su rol.
 *
 * Ocultar un boton es comodidad, no seguridad: el servidor vuelve a comprobar
 * el permiso en cada peticion. La interfaz pregunta por permisos y no por
 * roles para que un rol editado se refleje sin tocar ninguna pantalla.
 */
export function useCan(permission: PermissionCode): boolean {
  return useSession((state) => hasPermission(state.user, permission))
}
