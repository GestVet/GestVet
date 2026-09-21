import type { ReactNode } from 'react'
import { Link } from 'react-router'

import EmptyState from '../../components/EmptyState'
import Icon from '../../components/Icon'
import PageHeader from '../../components/PageHeader'
import { Button } from '../../components/ui/button'
import { useLayoutStore } from '../../store/layout'
import { useSession } from '../../store/session'
import DashboardAccesoCard from './DashboardAccesoCard'
import DashboardBlocksEditable from './DashboardBlocksEditable'
import {
  reorderDashboardBlocks,
  resolveDashboardBlocks,
  toggleDashboardBlock,
} from './dashboardAccesos'

export default function DashboardView() {
  const user = useSession((state) => state.user)
  const editMode = useLayoutStore((state) => state.editMode)
  const guardados = useLayoutStore((state) => state.dashboardBlocks)
  const setDashboardBlocks = useLayoutStore((state) => state.setDashboardBlocks)

  if (user === null) {
    return null
  }

  const bloques = resolveDashboardBlocks(guardados, user.permissions)
  const visibles = bloques.filter((bloque) => bloque.visible)
  let accesos: ReactNode

  if (editMode) {
    accesos = (
      <div className="flex flex-col gap-3">
        <p className="m-0 text-sm text-muted-foreground">
          Arrastra las tarjetas para ordenarlas y usa el ojo para mostrarlas u ocultarlas.
        </p>
        <DashboardBlocksEditable
          blocks={bloques}
          onReorder={(ids) => {
            setDashboardBlocks(reorderDashboardBlocks(bloques, ids))
          }}
          onToggleVisible={(id) => {
            setDashboardBlocks(toggleDashboardBlock(bloques, id))
          }}
        />
      </div>
    )
  } else if (visibles.length === 0) {
    accesos = (
      <EmptyState
        title="No hay tarjetas visibles"
        description="Usa Personalizar para volver a mostrarlas en el panel."
      />
    )
  } else {
    accesos = (
      <nav aria-label="Accesos del panel">
        <ul className="m-0 grid list-none gap-4 p-0 sm:grid-cols-2 lg:grid-cols-3">
          {visibles.map((bloque) => (
            <li key={bloque.id} className="h-full">
              <DashboardAccesoCard acceso={bloque.acceso} />
            </li>
          ))}
        </ul>
      </nav>
    )
  }

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title={`Hola, ${user.first_name}`}
        description={user.email}
        actions={
          <Button asChild variant="outline" size="lg" className="h-10 px-4">
            <Link to="/perfil">
              <Icon name="perfil" size={16} />
              <span>Editar perfil</span>
            </Link>
          </Button>
        }
      />
      {accesos}
    </div>
  )
}
