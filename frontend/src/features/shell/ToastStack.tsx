import { useNotifications } from '../../store/notifications'
import ToastItem from './ToastItem'

export default function ToastStack() {
  const toasts = useNotifications((state) => state.toasts)

  if (toasts.length === 0) {
    return null
  }

  return (
    <div className="toast-stack" role="status" aria-live="polite">
      {toasts.map((toast) => (
        <ToastItem key={toast.id} id={toast.id} tone={toast.tone} message={toast.message} />
      ))}
    </div>
  )
}
