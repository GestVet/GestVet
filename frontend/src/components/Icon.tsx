import { ICON_VIEWBOX, ICONS, type IconName } from './icons'

interface IconProps {
  readonly name: IconName
  /** Lado del cuadrado, en pixeles. Hereda el color del texto que lo rodea. */
  readonly size?: number
  /**
   * Texto para quien no ve el icono. Sin el, el icono queda oculto a los
   * lectores de pantalla, que es lo correcto cuando acompana a una etiqueta
   * que ya dice lo mismo.
   */
  readonly label?: string
  readonly className?: string
}

const DEFAULT_SIZE = 20

/**
 * El unico componente que dibuja iconos en el frontend.
 *
 * El trazo sale del registro de `icons.ts`, asi que cambiar un icono es editar
 * una linea alli y verlo propagado por cada pantalla. `IconName` viene del
 * mismo registro, de modo que pedir un icono inexistente no compila.
 */
export default function Icon({ name, size = DEFAULT_SIZE, label, className }: IconProps) {
  return (
    <svg
      className={className}
      width={size}
      height={size}
      viewBox={ICON_VIEWBOX}
      fill="currentColor"
      role={label ? 'img' : undefined}
      aria-label={label}
      aria-hidden={label ? undefined : true}
      focusable="false"
    >
      <path d={ICONS[name]} />
    </svg>
  )
}
