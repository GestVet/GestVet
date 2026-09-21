import { Outlet } from 'react-router'

import AccessibilityWidget from '../../components/AccessibilityWidget'
import { useLayoutStore } from '../../store/layout'
import { useSession } from '../../store/session'
import AppFooter from './AppFooter'
import Brand from './Brand'
import GuestHeader from './GuestHeader'
import LayoutEditControls from './LayoutEditControls'
import MobileMenu from './MobileMenu'
import { entriesFor, orderNavEntries } from './navigation'
import NavList from './NavList'
import NavListEditable from './NavListEditable'
import SessionActions from './SessionActions'
import ToastStack from './ToastStack'
import { useClientAppointmentAlerts } from './useClientAppointmentAlerts'
import { useLayoutPreferences } from './useLayoutPreferences'
import { useRealtimeUpdates } from './useRealtimeUpdates'
import { useVeterinarianEmergencyAlerts } from './useVeterinarianEmergencyAlerts'

/**
 * El armazon de todas las pantallas.
 *
 * Con sesion, el menu va en una barra lateral en pantallas anchas y detras de
 * un boton en las angostas: un administrador tiene nueve entradas y en una
 * barra superior no entraban ni en escritorio. Sin sesion basta la marca y
 * los dos accesos. El desbordamiento horizontal se recorta porque el heroe
 * de la landing se estira al ancho de la ventana.
 */
export default function AppShell() {
  const user = useSession((state) => state.user)
  const sidebarOrder = useLayoutStore((state) => state.sidebarOrder)
  const editMode = useLayoutStore((state) => state.editMode)
  useLayoutPreferences()
  useRealtimeUpdates()
  useClientAppointmentAlerts()
  useVeterinarianEmergencyAlerts()

  const invitados = user === null
  const content = (
    <>
      <AccessibilityWidget />
      <ToastStack />
      <main
        id="contenido"
        tabIndex={-1}
        className={
          invitados
            ? 'flex w-full flex-1 flex-col px-4 py-6 outline-none sm:px-6'
            : 'mx-auto w-full max-w-[1100px] flex-1 px-4 py-6 outline-none sm:px-6'
        }
      >
        <Outlet />
      </main>
      <AppFooter invitados={invitados} />
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
      <div className="landing flex min-h-screen flex-col overflow-x-clip bg-background font-sans text-foreground">
        {skipLink}
        <GuestHeader />
        {content}
      </div>
    )
  }

  const entries = orderNavEntries(entriesFor(user.permissions), sidebarOrder)

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[15rem_1fr]">
      {skipLink}
      {/* La columna pinta el fondo de punta a punta; adentro, el menú queda fijo al desplazarse. */}
      <div className="hidden border-r bg-card lg:block">
      <aside className="sticky top-0 flex h-screen flex-col gap-6 p-4">
        <div className="px-1 pt-1">
          <Brand to="/panel" />
        </div>
        <LayoutEditControls />
        <nav aria-label="Navegación principal" className="flex-1 overflow-y-auto">
          {editMode ? <NavListEditable entries={entries} /> : <NavList entries={entries} />}
        </nav>
        <SessionActions firstName={user.first_name} />
      </aside>
      </div>

      <div className="flex min-h-screen min-w-0 flex-col">
        <header className="sticky top-0 z-40 flex items-center justify-between gap-3 border-b bg-card px-4 py-1.5 lg:hidden">
          <Brand to="/panel" />
          <div className="flex items-center gap-1">
            <LayoutEditControls variant="toolbar" />
            <MobileMenu entries={entries} firstName={user.first_name} />
          </div>
        </header>
        {content}
      </div>
    </div>
  )
}
