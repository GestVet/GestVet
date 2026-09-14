import { Link } from 'react-router'

import { Button } from '../../components/ui/button'
import Brand from './Brand'
import GuestNav from './GuestNav'

/** La barra de quien todavia no inicio sesion. */
export default function GuestHeader() {
  return (
    <header className="sticky top-0 z-40 border-b bg-card">
      <div className="mx-auto flex max-w-[1100px] flex-wrap items-center gap-3 px-4 py-3 sm:px-6 md:flex-nowrap">
        <Brand to="/" />
        <GuestNav className="order-3 w-full md:order-none md:flex-1" />
        <Button asChild size="lg" className="ml-auto h-10 px-5 md:ml-0">
          <Link to="/acceso">Iniciar sesión</Link>
        </Button>
      </div>
    </header>
  )
}
