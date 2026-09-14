import FormMessage from '../../components/FormMessage'
import { useSession } from '../../store/session'

/**
 * Explica por qué se volvió al acceso cuando la sesión venció sola.
 *
 * Sin este aviso, quien tenía una pantalla abierta ve el formulario de acceso
 * de golpe y no sabe si hizo algo mal.
 */
export default function SessionExpiredNotice() {
  const expired = useSession((state) => state.expired)

  return (
    <div hidden={!expired}>
      <FormMessage tone="error">Tu sesión venció. Vuelve a entrar para seguir donde estabas.</FormMessage>
    </div>
  )
}
