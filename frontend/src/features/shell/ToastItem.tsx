import { useEffect } from 'react'

import Icon from '../../components/Icon'
import { useNotifications } from '../../store/notifications'

const AUTO_DISMISS_MS = 8_000

interface ToastItemProps {
  readonly id: string
  readonly tone: 'info' | 'warning'
  readonly message: string
}

export default function ToastItem({ id, tone, message }: ToastItemProps) {
  const dismiss = useNotifications((state) => state.dismiss)

  useEffect(() => {
    const temporizador = window.setTimeout(() => {
      dismiss(id)
    }, AUTO_DISMISS_MS)
    return () => {
      window.clearTimeout(temporizador)
    }
  }, [id, dismiss])

  return (
    <div className={`toast toast-${tone}`}>
      <Icon name="alerta" size={16} />
      <span>{message}</span>
      <button
        type="button"
        className="toast-close"
        aria-label="Descartar"
        onClick={() => {
          dismiss(id)
        }}
      >
        ×
      </button>
    </div>
  )
}
