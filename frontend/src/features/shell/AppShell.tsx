import { Link, NavLink, Outlet, useNavigate } from 'react-router'

import Icon from '../../components/Icon'
import { useSession } from '../../store/session'
import { entriesForRole } from './navigation'
import ToastStack from './ToastStack'
import { useClientAppointmentAlerts } from './useClientAppointmentAlerts'
import { useVeterinarianEmergencyAlerts } from './useVeterinarianEmergencyAlerts'

const ANIO = new Date().getFullYear()

function claseDeEnlace({ isActive }: { isActive: boolean }): string {
  return isActive ? 'is-active' : ''
}

export default function AppShell() {
  const user = useSession((state) => state.user)
  const signOut = useSession((state) => state.signOut)
  const navigate = useNavigate()
  useClientAppointmentAlerts()
  useVeterinarianEmergencyAlerts()

  const entradas = user === null ? [] : entriesForRole(user.role)

  const cerrarSesion = () => {
    signOut()
    void navigate('/')
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <Link className="brand" to={user === null ? '/' : '/panel'}>
          <Icon name="huella" size={28} />
          <span>GestVet</span>
        </Link>

        <nav className="nav-links" aria-label="Navegación principal">
          {entradas.map((entrada) => (
            <NavLink key={entrada.to} to={entrada.to} className={claseDeEnlace}>
              <Icon name={entrada.icon} size={16} />
              <span>{entrada.label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="session-box">
          {user === null ? (
            <>
              <Link className="btn btn-blue" to="/acceso">
                Iniciar sesión
              </Link>
              <Link className="btn btn-green" to="/registro">
                Registrarse
              </Link>
            </>
          ) : (
            <>
              <Link className="nav-links" to="/perfil">
                <Icon name="perfil" size={16} />
                <span className="session-name">{user.first_name}</span>
              </Link>
              <button type="button" className="btn btn-plain" onClick={cerrarSesion}>
                <Icon name="salir" size={16} />
                <span>Cerrar sesión</span>
              </button>
            </>
          )}
        </div>
      </header>

      <ToastStack />

      <main className="page-container">
        <Outlet />
      </main>

      <footer className="footer">
        © {ANIO} GestVet · Av. Prof. César Vallejo 95, Víctor Larco Herrera, Trujillo
      </footer>
    </div>
  )
}
