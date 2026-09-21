import Icon from '../../components/Icon'
import { Button } from '../../components/ui/button'
import { useLayoutStore } from '../../store/layout'
import LayoutEditToggle from './LayoutEditToggle'

interface LayoutEditControlsProps {
  /** `toolbar` solo muestra el interruptor; `bar` son las acciones del celular. */
  readonly variant?: 'sidebar' | 'toolbar' | 'bar'
}

/**
 * El interruptor de personalizacion y, en modo edicion, sus acciones.
 *
 * "Restablecer" borra lo guardado y "Listo" cierra el modo confirmando lo
 * pendiente sin esperar al guardado automatico. El estado del guardado se
 * anuncia en una region aria-live. La variante `bar` existe para que en el
 * celular las dos acciones esten a la vista sin abrir el menu: es una barra
 * fija abajo que termina antes del boton de accesibilidad, en la esquina
 * inferior derecha.
 */
export default function LayoutEditControls({ variant = 'sidebar' }: LayoutEditControlsProps) {
  const editMode = useLayoutStore((state) => state.editMode)
  const toggleEditMode = useLayoutStore((state) => state.toggleEditMode)
  const reset = useLayoutStore((state) => state.reset)
  const saving = useLayoutStore((state) => state.saving)
  const hayPreferencias = useLayoutStore(
    (state) => state.hasSaved || state.sidebarOrder.length > 0 || state.dashboardBlocks.length > 0,
  )
  const estado = saving ? 'Guardando…' : 'Los cambios se guardan solos.'
  const restablecer = () => {
    void reset()
  }

  if (variant === 'toolbar') {
    return <LayoutEditToggle variant="toolbar" />
  }
  if (!editMode) {
    return variant === 'bar' ? null : <LayoutEditToggle />
  }

  if (variant === 'bar') {
    return (
      <div role="region" aria-label="Acciones de personalización" className="fixed bottom-0 left-0 right-24 z-30 border-t bg-card px-3 pt-2 pb-[max(0.75rem,env(safe-area-inset-bottom))] lg:hidden">
        <div className="flex items-center gap-2">
          <p role="status" aria-live="polite" className="sr-only">{estado}</p>
          <Button type="button" variant="outline" size="sm" className="h-11 flex-1" disabled={!hayPreferencias} onClick={restablecer}>
            <Icon name="restablecer" size={14} />
            <span>Restablecer</span>
          </Button>
          <Button type="button" size="sm" className="h-11 flex-1" onClick={toggleEditMode}>
            <Icon name="confirmar" size={14} />
            <span>Listo</span>
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-2">
      <LayoutEditToggle />
      <div className="flex flex-col gap-2 rounded-xl border bg-card p-3">
        <p className="m-0 text-xs leading-relaxed text-muted-foreground">
          Arrastra para ordenar y usa las flechas de cada entrada para moverla. El ojo de
          una tarjeta la oculta o la vuelve a mostrar.
        </p>
        <div className="flex gap-2">
          <Button type="button" variant="outline" size="sm" className="flex-1 pointer-coarse:h-11" disabled={!hayPreferencias} onClick={restablecer}>
            <Icon name="restablecer" size={14} />
            <span>Restablecer</span>
          </Button>
          <Button type="button" size="sm" className="flex-1 pointer-coarse:h-11" onClick={toggleEditMode}>
            <Icon name="confirmar" size={14} />
            <span>Listo</span>
          </Button>
        </div>
        <p role="status" aria-live="polite" className="m-0 text-xs text-muted-foreground">{estado}</p>
      </div>
    </div>
  )
}
