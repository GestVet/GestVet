import { useEffect } from 'react'

import Icon from '../../components/Icon'
import { Button } from '../../components/ui/button'
import { useNotifications } from '../../store/notifications'

const AUTO_DISMISS_MS = 8_000

// El tono lo lleva el icono y no un borde de color: el texto queda siempre en
// el color de lectura, y el aviso se entiende igual sin distinguir colores.
const ICON_TONE = {
  info: 'text-primary',
  warning: 'text-warning',
} as const

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
    <div className="flex items-start gap-3 rounded-xl bg-card p-3 text-sm text-card-foreground shadow-lg ring-1 ring-foreground/10">
      <Icon name="alerta" size={18} className={`mt-0.5 shrink-0 ${ICON_TONE[tone]}`} />
      <p className="m-0 flex-1">{message}</p>
      <Button
        type="button"
        variant="ghost"
        size="icon"
        className="size-8 shrink-0 text-muted-foreground hover:text-foreground"
        aria-label="Descartar notificación"
        onClick={() => {
          dismiss(id)
        }}
      >
        <Icon name="cancelar" size={16} />
      </Button>
    </div>
  )
}
