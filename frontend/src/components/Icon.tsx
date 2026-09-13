import { ICONS, type IconName } from './icons'

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
const STROKE_WIDTH = 1.75

/**
 * El unico componente que dibuja iconos en el frontend.
 *
 * El icono sale del registro de `icons.ts`, asi que cambiarlo es editar una
 * linea alli y verlo propagado por cada pantalla. `IconName` viene del mismo
 * registro, de modo que pedir un icono inexistente no compila.
 */
export default function Icon({ name, size = DEFAULT_SIZE, label, className }: IconProps) {
  const Glyph = ICONS[name]

  return (
    <Glyph
      className={className}
      size={size}
      strokeWidth={STROKE_WIDTH}
      role={label ? 'img' : undefined}
      aria-label={label}
      aria-hidden={label ? undefined : true}
      focusable="false"
    />
  )
}
