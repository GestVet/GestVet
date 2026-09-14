import { Link, useNavigate } from 'react-router'

import Icon from '../../components/Icon'
import { Button } from '../../components/ui/button'
import { useSession } from '../../store/session'

interface SessionActionsProps {
  readonly firstName: string
  readonly onNavigate?: () => void
}

/** El perfil propio y la salida, al pie de la barra lateral y del menu. */
export default function SessionActions({ firstName, onNavigate }: SessionActionsProps) {
  const signOut = useSession((state) => state.signOut)
  const navigate = useNavigate()

  const cerrarSesion = async () => {
    onNavigate?.()
    // Hay que salir de la pantalla privada antes de vaciar la sesion. El router
    // aplica la navegacion dentro de una transicion, asi que esperar la promesa
    // no alcanza: la guarda sigue montada, ve la sesion vacia y redirige al
    // inicio de sesion. `flushSync` deja la portada dibujada antes de seguir.
    await navigate('/', { flushSync: true })
    signOut()
  }

  return (
    <div className="flex flex-col gap-1 border-t pt-3">
      <Button asChild variant="ghost" className="h-10 justify-start gap-3 px-3">
        <Link to="/perfil" onClick={onNavigate}>
          <Icon name="perfil" size={18} />
          <span className="truncate">{firstName}</span>
        </Link>
      </Button>
      <Button
        type="button"
        variant="ghost"
        className="h-10 justify-start gap-3 px-3"
        onClick={() => {
          void cerrarSesion()
        }}
      >
        <Icon name="salir" size={18} />
        <span>Cerrar sesión</span>
      </Button>
    </div>
  )
}
