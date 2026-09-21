import Icon from '../../components/Icon'
import SortableList from '../../components/SortableList'
import { Button } from '../../components/ui/button'
import DashboardAccesoCard from './DashboardAccesoCard'
import type { DashboardBlockView } from './dashboardAccesos'

interface DashboardBlocksEditableProps {
  readonly blocks: readonly DashboardBlockView[]
  readonly onReorder: (ids: readonly string[]) => void
  readonly onToggleVisible: (id: string) => void
}

/**
 * La rejilla del panel mientras se personaliza.
 *
 * Se ven todas las tarjetas, tambien las ocultas, atenuadas: si desaparecieran
 * no habria como volver a mostrarlas. El ojo de cada una alterna su
 * visibilidad y el asa o los botones cambian el orden.
 */
export default function DashboardBlocksEditable({
  blocks,
  onReorder,
  onToggleVisible,
}: DashboardBlocksEditableProps) {
  return (
    <SortableList
      items={blocks}
      getId={(block) => block.id}
      getLabel={(block) => block.acceso.title}
      onReorder={onReorder}
      shape="grid"
      className="m-0 grid list-none gap-4 p-0 sm:grid-cols-2 lg:grid-cols-3"
      itemClassName="h-full"
      renderItem={(block) => (
        <DashboardAccesoCard
          acceso={block.acceso}
          estatica
          oculto={!block.visible}
          accion={
            <Button
              type="button"
              variant="ghost"
              size="icon-sm"
              aria-pressed={!block.visible}
              aria-label={
                block.visible
                  ? `Ocultar ${block.acceso.title}`
                  : `Mostrar ${block.acceso.title}`
              }
              onClick={() => {
                onToggleVisible(block.id)
              }}
            >
              <Icon name={block.visible ? 'ocultar' : 'ver'} size={16} />
            </Button>
          }
        />
      )}
    />
  )
}
