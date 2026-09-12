import { Outlet } from 'react-router'

import { useSession } from '../../store/session'
import Brand from './Brand'
import GuestHeader from './GuestHeader'
import MobileMenu from './MobileMenu'
import { entriesForRole } from './navigation'
import NavList from './NavList'
import SessionActions from './SessionActions'
import ToastStack from './ToastStack'
import { useClientAppointmentAlerts } from './useClientAppointmentAlerts'
import { useVeterinarianEmergencyAlerts } from './useVeterinarianEmergencyAlerts'

const ANIO = new Date().getFullYear()

/**
 * El armazon de todas las pantallas.
 *
 * Con sesion, el menu va en una barra lateral en pantallas anchas y detras de
 * un boton en las angostas: un administrador tiene nueve entradas y en una
 * barra superior no entraban ni en escritorio. Sin sesion basta la marca y
 * los dos accesos.
 */
export default function AppShell() {
  const user = useSession((state) => state.user)
  useClientAppointmentAlerts()
  useVeterinarianEmergencyAlerts()

  const content = (
    <>
      <ToastStack />
      <main
        id="contenido"
        tabIndex={-1}
        className="mx-auto w-full max-w-[1100px] flex-1 px-4 py-6 outline-none sm:px-6"
      >
        <Outlet />
      </main>
      <footer className="border-t px-4 py-4 text-center text-sm text-muted-foreground">
        © {ANIO} GestVet · Av. Prof. César Vallejo 95, Víctor Larco Herrera, Trujillo
      </footer>
    </>
  )

  const skipLink = (
    <a
      href="#contenido"
      className="sr-only rounded-lg bg-primary px-3 py-2 text-primary-foreground focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-50"
    >
      Saltar al contenido
    </a>
  )

  if (user === null) {
    return (
      <div className="flex min-h-screen flex-col">
        {skipLink}
        <GuestHeader />
        {content}
      </div>
    )
  }

  const entries = entriesForRole(user.role)

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[15rem_1fr]">
      {skipLink}
      <aside className="hidden border-r bg-card lg:sticky lg:top-0 lg:flex lg:h-screen lg:flex-col lg:gap-6 lg:p-4">
        <div className="px-1 pt-1">
          <Brand to="/panel" />
        </div>
        <nav aria-label="Navegación principal" className="flex-1 overflow-y-auto">
          <NavList entries={entries} />
        </nav>
        <SessionActions firstName={user.first_name} />
      </aside>

      <div className="flex min-h-screen min-w-0 flex-col">
        <header className="sticky top-0 z-40 flex items-center justify-between gap-3 border-b bg-card px-4 py-1.5 lg:hidden">
          <Brand to="/panel" />
          <MobileMenu entries={entries} firstName={user.first_name} />
        </header>
        {content}
      </div>
    </div>
  )
}
