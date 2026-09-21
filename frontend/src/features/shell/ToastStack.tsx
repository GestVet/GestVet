import { useNotifications } from '../../store/notifications'
import ToastItem from './ToastItem'

export default function ToastStack() {
  const toasts = useNotifications((state) => state.toasts)

  if (toasts.length === 0) {
    return null
  }

  // La columna se corre a la izquierda del botón de accesibilidad, que vive
  // fijo en la esquina inferior derecha (ver index.html): por más avisos que
  // se apilen, ninguno queda debajo del botón ni de su "Descartar". La
  // separación es horizontal y no vertical, así no depende de cuántos avisos
  // haya en pantalla.
  return (
    <div
      className="fixed right-24 bottom-4 z-50 flex w-[min(22rem,calc(100vw-8rem))] flex-col gap-2 pointer-events-none"
      role="status"
      aria-live="polite"
      aria-label="Avisos del sistema"
    >
      {toasts.map((toast) => (
        <div key={toast.id} className="pointer-events-auto">
          <ToastItem id={toast.id} tone={toast.tone} message={toast.message} />
        </div>
      ))}
    </div>
  )
}
