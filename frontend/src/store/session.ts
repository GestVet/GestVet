import { create } from 'zustand'

import { setAuthToken } from '../services/api'
import { logger } from '../services/logger'
import type {
  AccessTokenResponse,
  CurrentUserResponse,
  PermissionCode,
  UserResponse,
} from '../api/types'

// La version va en la clave: una sesion guardada antes de existir los permisos
// no los trae, y leerla como si los tuviera dejaria la interfaz sin menu.
const STORAGE_KEY = 'gestvet.session.v2'

interface StoredSession {
  token: string
  user: CurrentUserResponse
}

interface SessionState {
  token: string | null
  user: CurrentUserResponse | null
  signIn: (response: AccessTokenResponse) => void
  /** Aplica un perfil nuevo. Si la respuesta no trae permisos, se conservan los que habia. */
  updateUser: (user: UserResponse | CurrentUserResponse) => void
  signOut: () => void
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

const restored = readStoredSession()
setAuthToken(restored?.token ?? null)

export const useSession = create<SessionState>((set) => ({
  token: restored?.token ?? null,
  user: restored?.user ?? null,

  signIn: (response) => {
    setAuthToken(response.access_token)
    writeStoredSession({ token: response.access_token, user: response.user })
    set({ token: response.access_token, user: response.user })
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
    setAuthToken(null)
    writeStoredSession(null)
    set({ token: null, user: null })
    logger.info('auth.signed_out')
  },
}))

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
