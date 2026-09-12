import { useNotifications } from '../../store/notifications'
import ToastItem from './ToastItem'

export default function ToastStack() {
  const toasts = useNotifications((state) => state.toasts)

  if (toasts.length === 0) {
    return null
  }

  return (
    <div
      className="fixed right-4 bottom-4 z-50 flex w-[min(22rem,calc(100vw-2rem))] flex-col gap-2"
      role="status"
      aria-live="polite"
    >
      {toasts.map((toast) => (
        <ToastItem key={toast.id} id={toast.id} tone={toast.tone} message={toast.message} />
      ))}
    </div>
  )
}
