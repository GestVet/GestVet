import { create } from 'zustand'

import { setAuthToken } from '../services/api'
import type { AccessTokenResponse, UserResponse } from '../api/types'

const STORAGE_KEY = 'gestvet.session'

interface StoredSession {
  token: string
  user: UserResponse
}

interface SessionState {
  token: string | null
  user: UserResponse | null
  signIn: (response: AccessTokenResponse) => void
  updateUser: (user: UserResponse) => void
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
  },

  updateUser: (user) => {
    set((state) => {
      if (state.token !== null) {
        writeStoredSession({ token: state.token, user })
      }
      return { user }
    })
  },

  signOut: () => {
    setAuthToken(null)
    writeStoredSession(null)
    set({ token: null, user: null })
  },
}))

// Selectores con nombre. Preguntar "es veterinario" en cada pantalla obligaba
// a repetir la comparacion contra dos roles, y la regla de complejidad lo
// contaba en cada componente.
const ROLES_QUE_ATIENDEN = new Set(['veterinarian', 'emergency_veterinarian'])
const ROLES_DE_PERSONAL = new Set(['admin', 'veterinarian', 'emergency_veterinarian'])

export function useIsVeterinarian(): boolean {
  return useSession((state) => state.user !== null && ROLES_QUE_ATIENDEN.has(state.user.role))
}

export function useIsAdmin(): boolean {
  return useSession((state) => state.user?.role === 'admin')
}

export function useIsStaff(): boolean {
  return useSession((state) => state.user !== null && ROLES_DE_PERSONAL.has(state.user.role))
}
