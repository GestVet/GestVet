import Icon from '../../components/Icon'
import { Button } from '../../components/ui/button'
import { useLayoutStore } from '../../store/layout'
import LayoutEditToggle from './LayoutEditToggle'

interface LayoutEditControlsProps {
  /** `toolbar` solo muestra el interruptor, para la barra del celular. */
  readonly variant?: 'sidebar' | 'toolbar'
}

/**
 * El interruptor de personalizacion y, en modo edicion, sus acciones.
 *
 * "Restablecer" borra lo guardado y "Listo" cierra el modo confirmando lo
 * pendiente sin esperar al guardado automatico. El estado del guardado se
 * anuncia en una region aria-live.
 */
export default function LayoutEditControls({ variant = 'sidebar' }: LayoutEditControlsProps) {
  const editMode = useLayoutStore((state) => state.editMode)
  const toggleEditMode = useLayoutStore((state) => state.toggleEditMode)
  const reset = useLayoutStore((state) => state.reset)
  const saving = useLayoutStore((state) => state.saving)
  const hayPreferencias = useLayoutStore(
    (state) =>
      state.hasSaved || state.sidebarOrder.length > 0 || state.dashboardBlocks.length > 0,
  )

  const enBarra = variant === 'toolbar'

  if (enBarra || !editMode) {
    return <LayoutEditToggle variant={variant} />
  }

  return (
    <div className="flex flex-col gap-2">
      <LayoutEditToggle />
      <div className="flex flex-col gap-2 rounded-xl border bg-card p-3">
        <p className="m-0 text-xs leading-relaxed text-muted-foreground">
          Arrastra las entradas para ordenarlas y usa el ojo para ocultar tarjetas. Se
          guarda solo.
        </p>
        <div className="flex gap-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="flex-1"
            disabled={!hayPreferencias}
            onClick={() => {
              void reset()
            }}
          >
            <Icon name="restablecer" size={14} />
            <span>Restablecer</span>
          </Button>
          <Button type="button" size="sm" className="flex-1" onClick={toggleEditMode}>
            <Icon name="confirmar" size={14} />
            <span>Listo</span>
          </Button>
        </div>
        <p role="status" aria-live="polite" className="m-0 text-xs text-muted-foreground">
          {saving ? 'Guardando…' : 'Los cambios se guardan solos.'}
        </p>
      </div>
    </div>
  )
}
