import { useEffect } from 'react'

import { useLayoutStore } from '../../store/layout'
import { useNotifications } from '../../store/notifications'
import { useSession } from '../../store/session'

/**
 * Conecta la personalizacion con la sesion y con los avisos.
 *
 * Al entrar se pide la preferencia guardada y al salir se vacia, para que la
 * cuenta siguiente no herede el orden de la anterior. Si un guardado falla, el
 * aviso sale una sola vez y el estado local se conserva: el proximo cambio
 * vuelve a intentar con el estado completo.
 */
export function useLayoutPreferences(): void {
  const token = useSession((state) => state.token)
  const saveError = useLayoutStore((state) => state.saveError)
  const push = useNotifications((state) => state.push)
  const clearSaveError = useLayoutStore((state) => state.clearSaveError)

  useEffect(() => {
    if (token === null) {
      useLayoutStore.getState().clear()
      return
    }
    void useLayoutStore.getState().load()
  }, [token])

  useEffect(() => {
    if (saveError === null) {
      return
    }
    push({ tone: 'warning', message: saveError.message })
    clearSaveError()
  }, [saveError, push, clearSaveError])
}
