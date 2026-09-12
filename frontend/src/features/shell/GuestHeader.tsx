import { Link } from 'react-router'

import { Button } from '../../components/ui/button'
import Brand from './Brand'

/** La barra de quien todavia no inicio sesion. */
export default function GuestHeader() {
  return (
    <header className="border-b bg-card">
      <div className="mx-auto flex max-w-[1100px] flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-6">
        <Brand to="/" />
        <div className="flex items-center gap-2">
          <Button asChild variant="outline" size="lg" className="h-10 px-4">
            <Link to="/acceso">Iniciar sesión</Link>
          </Button>
          <Button asChild variant="success" size="lg" className="h-10 px-4">
            <Link to="/registro">Registrarse</Link>
          </Button>
        </div>
      </div>
    </header>
  )
}
