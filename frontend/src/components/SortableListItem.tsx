import { useSortable } from '@dnd-kit/sortable'
import { cn } from 'cn'
import type { CSSProperties, ReactNode } from 'react'

import { usePrefersReducedMotion } from '../hooks/usePrefersReducedMotion'
import Icon from './Icon'

const BOTON_FLECHA =
  'flex size-7 items-center justify-center rounded-md text-muted-foreground outline-none hover:bg-muted hover:text-foreground focus-visible:ring-3 focus-visible:ring-ring/50 disabled:pointer-events-none disabled:opacity-40 pointer-coarse:size-11 max-lg:size-11'

const ASA =
  'flex w-7 shrink-0 cursor-grab touch-none items-center justify-center rounded-lg text-muted-foreground outline-none hover:bg-muted hover:text-foreground focus-visible:ring-3 focus-visible:ring-ring/50 active:cursor-grabbing pointer-coarse:w-11 pointer-coarse:rounded-xl max-lg:w-11'

interface SortableListItemProps {
  readonly id: string
  /** Nombra la entrada en las etiquetas de sus controles. */
  readonly label: string
  readonly position: number
  readonly total: number
  /** Cuanto se desplaza: -1 sube un lugar, 1 baja uno. */
  readonly onMove: (delta: number) => void
  readonly children: ReactNode
  readonly className?: string
}

/**
 * Una fila reordenable.
 *
 * El asa es lo unico que levanta el elemento: los controles de subir y bajar
 * conviven con el contenido y son la alternativa de un solo puntero que pide
 * el criterio 2.5.7 de WCAG. La posicion va en texto oculto para que el lector
 * de pantalla la lea al recorrer la lista. Con puntero fino los controles miden
 * 28px; en puntero grueso, o en pantalla angosta, pasan a 44px para poder
 * tocarlos sin apuntar con precision.
 */
export default function SortableListItem({
  id,
  label,
  position,
  total,
  onMove,
  children,
  className,
}: SortableListItemProps) {
  const reduce = usePrefersReducedMotion()
  const { attributes, listeners, setNodeRef, setActivatorNodeRef, transform, transition, isDragging } =
    useSortable({ id, transition: reduce ? null : undefined })

  const estilo: CSSProperties | undefined =
    transform === null
      ? undefined
      : {
          transform: `translate3d(${String(transform.x)}px, ${String(transform.y)}px, 0)`,
          transition,
        }

  return (
    <li
      ref={setNodeRef}
      style={estilo}
      data-dragging={isDragging ? 'true' : undefined}
      className={cn('relative flex items-stretch gap-1', isDragging && 'z-10', className)}
    >
      <button
        type="button"
        ref={setActivatorNodeRef}
        {...attributes}
        {...listeners}
        aria-label={`Mover ${label}`}
        className={ASA}
      >
        <Icon name="arrastrar" size={16} />
      </button>

      <div className={cn('min-w-0 flex-1', isDragging && 'opacity-80')}>{children}</div>

      <div className="flex shrink-0 flex-col justify-center gap-1">
        <button
          type="button"
          className={BOTON_FLECHA}
          aria-label={`Subir ${label}`}
          disabled={position === 0}
          onClick={() => {
            onMove(-1)
          }}
        >
          <Icon name="subir" size={15} />
        </button>
        <button
          type="button"
          className={BOTON_FLECHA}
          aria-label={`Bajar ${label}`}
          disabled={position === total - 1}
          onClick={() => {
            onMove(1)
          }}
        >
          <Icon name="bajar" size={15} />
        </button>
      </div>

      <p className="sr-only">{`Posición ${String(position + 1)} de ${String(total)}.`}</p>
    </li>
  )
}
