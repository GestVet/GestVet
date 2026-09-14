interface GestVetMarkProps {
  readonly size?: number
  readonly className?: string
}

/**
 * El icono oficial de la marca GestVet: huella blanca con corazon calado
 * sobre un fondo cuadrado redondeado con gradiente azul/cian (Imagen 3).
 */
export default function GestVetMark({ size = 36, className = '' }: GestVetMarkProps) {
  const sizePx = `${size.toString()}px`

  return (
    <img
      src="/gestvet-icon.png"
      alt="GestVet Logo"
      width={size}
      height={size}
      className={`rounded-xl object-contain shadow-sm ${className}`}
      style={{ width: sizePx, height: sizePx }}
    />
  )
}

