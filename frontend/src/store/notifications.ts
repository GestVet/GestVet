import { create } from 'zustand'

export interface Toast {
  readonly id: string
  readonly tone: 'info' | 'warning'
  readonly message: string
}

interface NotificationsState {
  toasts: readonly Toast[]
  push: (toast: Omit<Toast, 'id'>) => void
  dismiss: (id: string) => void
}

/**
 * Avisos no bloqueantes en pantalla.
 *
 * El original mostraba un `alert()`, que corta la interacción hasta que
 * alguien lo cierra. Acá el aviso se apila y desaparece solo, sin bloquear
 * nada: quien esté completando otra cosa no pierde lo que estaba haciendo.
 */
export const useNotifications = create<NotificationsState>((set) => ({
  toasts: [],

  push: (toast) => {
    const id = crypto.randomUUID()
    set((state) => ({ toasts: [...state.toasts, { ...toast, id }] }))
  },

  dismiss: (id) => {
    set((state) => ({ toasts: state.toasts.filter((toast) => toast.id !== id) }))
  },
}))
