import { cn } from 'cn'
import { Suspense, lazy } from 'react'
import { Outlet } from 'react-router'

import AccessibilityWidget from '../../components/AccessibilityWidget'
import SortableSkeleton from '../../components/SortableSkeleton'
import { useLayoutStore } from '../../store/layout'
import { useSession } from '../../store/session'
import AppFooter from './AppFooter'
import Brand from './Brand'
import GuestHeader from './GuestHeader'
import LayoutEditControls from './LayoutEditControls'
import MobileMenu from './MobileMenu'
import { entriesFor, orderNavEntries } from './navigation'
import NavList from './NavList'
import SessionActions from './SessionActions'
import ToastStack from './ToastStack'
import { useClientAppointmentAlerts } from './useClientAppointmentAlerts'
import { useClientConsentAlerts } from './useClientConsentAlerts'
import { useLayoutPreferences } from './useLayoutPreferences'
import { useRealtimeUpdates } from './useRealtimeUpdates'
import { useVeterinarianEmergencyAlerts } from './useVeterinarianEmergencyAlerts'

// El editor del menu trae @dnd-kit, que pesa mas que toda la pantalla. Se pide
// recien al entrar en modo edicion; hasta entonces viaja en su propio fragmento.
const NavListEditable = lazy(() => import('./NavListEditable'))

// Es estatico: se crea una vez y no depende de props ni del estado.
const SKIP_LINK = (
  <a
    href="#contenido"
    className="sr-only rounded-lg bg-primary px-3 py-2 text-primary-foreground focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-50"
  >
    Saltar al contenido
  </a>
)

/**
 * El armazon de todas las pantallas.
 *
 * Con sesion, el menu va en una barra lateral en pantallas anchas y detras de
 * un boton en las angostas: un administrador tiene nueve entradas y en una
 * barra superior no entraban ni en escritorio. Sin sesion basta la marca y
 * los dos accesos. El desbordamiento horizontal se recorta porque el heroe
 * de la landing se estira al ancho de la ventana.
 *
 * En modo edicion y pantalla angosta, "Restablecer" y "Listo" viven en una
 * barra fija abajo, a la vista sin abrir el menu. La barra termina antes del
 * boton de accesibilidad, que ocupa la esquina inferior derecha, y el
 * contenido reserva su alto para que nada quede tapado.
 */
export default function AppShell() {
  const user = useSession((state) => state.user)
  const sidebarOrder = useLayoutStore((state) => state.sidebarOrder)
  const editMode = useLayoutStore((state) => state.editMode)
  useLayoutPreferences()
  useRealtimeUpdates()
  useClientAppointmentAlerts()
  useClientConsentAlerts()
  useVeterinarianEmergencyAlerts()

  const invitados = user === null
  const content = (
    <>
      <AccessibilityWidget />
      <ToastStack />
      <main
        id="contenido"
        tabIndex={-1}
        className={cn(
          'flex-1 px-4 py-6 outline-none sm:px-6',
          invitados ? 'flex w-full flex-col' : 'mx-auto w-full max-w-[1100px]',
          editMode && 'pb-28 lg:pb-6',
        )}
      >
        <Outlet />
      </main>
      <AppFooter invitados={invitados} />
    </>
  )

  if (user === null) {
    return (
      <div className="landing flex min-h-screen flex-col overflow-x-clip bg-background font-sans text-foreground">
        {SKIP_LINK}
        <GuestHeader />
        {content}
      </div>
    )
  }

  const entries = orderNavEntries(entriesFor(user.permissions), sidebarOrder)

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[15rem_1fr]">
      {SKIP_LINK}
      {/* La columna pinta el fondo de punta a punta; adentro, el menú queda fijo al desplazarse. */}
      <div className="hidden border-r bg-card lg:block">
      <aside className="sticky top-0 flex h-screen flex-col gap-6 p-4">
        <div className="px-1 pt-1">
          <Brand to="/panel" />
        </div>
        <LayoutEditControls />
        <nav aria-label="Navegación principal" className="flex-1 overflow-y-auto">
          {editMode ? (
            <Suspense fallback={<SortableSkeleton rows={entries.length} />}>
              <NavListEditable entries={entries} />
            </Suspense>
          ) : (
            <NavList entries={entries} />
          )}
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

      <LayoutEditControls variant="bar" />
    </div>
  )
}
