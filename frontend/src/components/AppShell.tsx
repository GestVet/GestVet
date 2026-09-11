import { Link, NavLink, Outlet } from 'react-router'

export default function AppShell() {
  return (
    <div className="app-shell">
      <header className="topbar">
        <Link className="brand" to="/">
          <span className="brand-mark">G</span>
          <span>GestVet</span>
        </Link>
        <nav className="nav-links" aria-label="Navegación principal">
          <NavLink to="/">Inicio</NavLink>
        </nav>
      </header>

      <main className="page-container">
        <Outlet />
      </main>
    </div>
  )
}
