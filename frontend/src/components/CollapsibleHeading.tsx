import type { ReactNode } from 'react'

import Icon from './Icon'

type Nivel = 'h2' | 'h3' | 'h4'

const TAMAÑOS: Record<Nivel, string> = {
  h2: 'text-lg',
  h3: 'text-lg',
  h4: 'text-base',
}

interface CollapsibleHeadingProps {
  readonly title: string
  readonly as: Nivel
  readonly description?: ReactNode
  readonly open: boolean
  readonly onToggle: () => void
  /** El `id` del contenido que abre y cierra. */
  readonly controls: string
}

/**
 * Un título que abre y cierra su sección.
 *
 * El botón va dentro del encabezado y no al revés: así el lector de pantalla
 * sigue encontrando la sección al recorrer los títulos, y además anuncia si
 * está abierta. La flecha gira, pero sin animación si la persona la desactivó.
 */
export default function CollapsibleHeading({
  title,
  as,
  description,
  open,
  onToggle,
  controls,
}: CollapsibleHeadingProps) {
  const Heading = as

  return (
    <div className="flex min-w-0 flex-1 flex-col gap-1">
      <Heading className={`m-0 font-heading leading-snug font-semibold text-foreground ${TAMAÑOS[as]}`}>
        <button
          type="button"
          aria-expanded={open}
          aria-controls={controls}
          onClick={onToggle}
          className="-mx-1 flex items-center gap-1.5 rounded-md px-1 text-left outline-none hover:text-primary focus-visible:ring-3 focus-visible:ring-ring/50"
        >
          <span
            className={`inline-flex shrink-0 text-muted-foreground transition-transform motion-reduce:transition-none ${open ? 'rotate-90' : ''}`}
          >
            <Icon name="siguiente" size={18} />
          </span>
          <span>{title}</span>
        </button>
      </Heading>
      {description === undefined ? null : (
        <p className="m-0 text-sm text-muted-foreground">{description}</p>
      )}
    </div>
  )
}
