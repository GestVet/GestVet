import { useState } from 'react'

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
 * Se ven todas las tarjetas, tambien las ocultas, que se marcan con "Oculta" y
 * un borde punteado: si desaparecieran no habria como volver a mostrarlas. El
 * ojo dice la accion, no el estado ("Ocultar X" cuando la tarjeta se ve,
 * "Mostrar X" cuando esta oculta), y la variante del boton acompana: la de una
 * tarjeta oculta se resalta para traerla de vuelta. Como la accion no lleva
 * `aria-pressed`, el resultado se anuncia por una region aria-live.
 */
export default function DashboardBlocksEditable({
  blocks,
  onReorder,
  onToggleVisible,
}: DashboardBlocksEditableProps) {
  const [anuncio, setAnuncio] = useState('')

  return (
    <>
      <SortableList
        items={blocks}
        getId={(block) => block.id}
        getLabel={(block) => block.acceso.title}
        onReorder={onReorder}
        shape="grid"
        className="m-0 grid list-none gap-4 p-0 sm:grid-cols-2 lg:grid-cols-3"
        itemClassName="h-full"
        renderItem={(block) => {
          const etiqueta = block.visible
            ? `Ocultar ${block.acceso.title}`
            : `Mostrar ${block.acceso.title}`
          return (
            <DashboardAccesoCard
              acceso={block.acceso}
              estatica
              oculto={!block.visible}
              accion={
                <Button
                  type="button"
                  variant={block.visible ? 'ghost' : 'outline'}
                  size="icon-sm"
                  className="pointer-coarse:size-11 max-lg:size-11"
                  title={etiqueta}
                  aria-label={etiqueta}
                  onClick={() => {
                    const texto = block.visible
                      ? `${block.acceso.title} oculta.`
                      : `${block.acceso.title} visible.`
                    setAnuncio((previo) => (previo === texto ? `${texto}\u00A0` : texto))
                    onToggleVisible(block.id)
                  }}
                >
                  <Icon name={block.visible ? 'ocultar' : 'ver'} size={16} />
                </Button>
              }
            />
          )
        }}
      />
      <p role="status" aria-live="polite" className="sr-only">
        {anuncio}
      </p>
    </>
  )
}
