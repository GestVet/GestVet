import { useQueryClient } from '@tanstack/react-query'
import { NavLink } from 'react-router'

import Icon from '../../components/Icon'
import type { NavEntry } from './navigation'
import { prefetchRoute } from './routePrefetch'

interface NavListProps {
  readonly entries: readonly NavEntry[]
  /** Lo usa el menu del celular para cerrarse al elegir una pantalla. */
  readonly onNavigate?: () => void
}

const BASE =
  'flex min-h-10 items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium outline-none transition-colors focus-visible:ring-3 focus-visible:ring-ring/50'

function linkClass({ isActive }: { isActive: boolean }): string {
  return isActive
    ? `${BASE} bg-primary text-primary-foreground`
    : `${BASE} text-foreground hover:bg-muted`
}

/**
 * Las entradas del menu, en columna.
 *
 * La misma lista sirve a la barra lateral y al menu del celular. NavLink marca
 * la pantalla actual con `aria-current`, asi que el lector de pantalla la
 * anuncia sin depender del color. Cada entrada precarga los datos de su
 * pantalla en cuanto la persona muestra intencion de abrirla.
 */
export default function NavList({ entries, onNavigate }: NavListProps) {
  const queryClient = useQueryClient()

  return (
    <ul className="m-0 flex list-none flex-col gap-1 p-0">
      {entries.map((entry) => {
        const precargar = () => {
          prefetchRoute(queryClient, entry.to)
        }
        return (
          <li key={entry.to}>
            <NavLink
              to={entry.to}
              className={linkClass}
              onClick={onNavigate}
              onMouseEnter={precargar}
              onFocus={precargar}
              onTouchStart={precargar}
            >
              <Icon name={entry.icon} size={18} />
              <span>{entry.label}</span>
            </NavLink>
          </li>
        )
      })}
    </ul>
  )
}
