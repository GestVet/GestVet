import Icon from '../../components/Icon'
import { Button } from '../../components/ui/button'
import { useLayoutStore } from '../../store/layout'

interface LayoutEditToggleProps {
  /** `toolbar` es solo el interruptor en icono, para la barra del celular. */
  readonly variant?: 'sidebar' | 'toolbar'
}

function varianteDe(enBarra: boolean, editMode: boolean): 'default' | 'ghost' | 'outline' {
  if (editMode) {
    return 'default'
  }
  return enBarra ? 'ghost' : 'outline'
}

/**
 * El interruptor de personalizacion.
 *
 * Es un boton de alternancia: `aria-pressed` dice si el modo de edicion esta
 * activo, asi que el lector de pantalla lo anuncia como encendido o apagado.
 * La etiqueta no cambia con el estado: con `aria-pressed` presente, un texto
 * que va y viene ("Personalizar" / "Personalizando") se anunciaria como un
 * nombre distinto y rompe la consistencia. El estado lo dice el color
 * (`bg-primary`, el azul de la marca) y, para quien no lo ve, `aria-pressed`.
 */
export default function LayoutEditToggle({ variant = 'sidebar' }: LayoutEditToggleProps) {
  const editMode = useLayoutStore((state) => state.editMode)
  const toggleEditMode = useLayoutStore((state) => state.toggleEditMode)
  const enBarra = variant === 'toolbar'
  const etiqueta = 'Personalizar'

  return (
    <Button
      type="button"
      variant={varianteDe(enBarra, editMode)}
      size={enBarra ? 'icon-lg' : 'default'}
      className={enBarra ? 'size-11' : 'h-10 w-full justify-start gap-3 px-3'}
      aria-pressed={editMode}
      aria-label={enBarra ? etiqueta : undefined}
      onClick={toggleEditMode}
    >
      <Icon name="personalizar" size={enBarra ? 20 : 18} />
      {enBarra ? null : <span>{etiqueta}</span>}
    </Button>
  )
}
