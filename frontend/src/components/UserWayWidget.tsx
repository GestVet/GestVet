import { useEffect } from 'react'

/**
 * Widget de accesibilidad UserWay.
 * Carga el script oficial de UserWay que despliega el botón flotante
 * de accesibilidad (icono azul con persona) en la esquina inferior.
 */
export default function UserWayWidget() {
  useEffect(() => {
    const envAccountId = import.meta.env.VITE_USERWAY_ACCOUNT_ID as string | undefined
    const accountId = envAccountId ?? 'demo'
    const scriptId = 'userway-widget-script'

    if (document.getElementById(scriptId) !== null) {
      return
    }

    const script = document.createElement('script')
    script.id = scriptId
    script.src = 'https://cdn.userway.org/widget.js'
    script.setAttribute('data-account', accountId)
    script.async = true
    document.body.appendChild(script)
  }, [])

  return null
}

