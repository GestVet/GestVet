interface GestVetMarkProps {
  readonly size?: number
  readonly className?: string
  /**
   * Texto alternativo. Vacío (y por eso decorativo) cuando el icono acompaña
   * al nombre de la marca, que ya lo anuncia; con texto para uso aislado.
   */
  readonly alt?: string
}

/**
 * El icono oficial de la marca GestVet: huella blanca con corazón calado
 * sobre un fondo cuadrado redondeado con gradiente azul/cian (Imagen 3).
 */
export default function GestVetMark({ size = 36, className = '', alt = '' }: GestVetMarkProps) {
  const sizePx = `${size.toString()}px`
  const decorativo = alt === ''

  return (
    <img
      src="/gestvet-icon.png"
      alt={alt}
      aria-hidden={decorativo}
      width={size}
      height={size}
      decoding="async"
      className={`rounded-xl object-contain shadow-sm ${className}`}
      style={{ width: sizePx, height: sizePx }}
    />
  )
}

