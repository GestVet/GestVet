import {
  DndContext,
  KeyboardSensor,
  PointerSensor,
  closestCenter,
  useSensor,
  useSensors,
  type Announcements,
  type DragEndEvent,
  type ScreenReaderInstructions,
  type UniqueIdentifier,
} from '@dnd-kit/core'
import {
  SortableContext,
  arrayMove,
  rectSortingStrategy,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable'
import { useState, type ReactNode } from 'react'

import SortableListItem from './SortableListItem'

// Distancia que hay que mover el puntero antes de que empiece un arrastre. Sin
// ella, un toque en el asa dispara el arrastre y la lista deja de desplazarse
// con el dedo.
const ACTIVACION_PX = 8

const INSTRUCCIONES: ScreenReaderInstructions = {
  draggable:
    'Para mover una entrada, enfoca su asa y presiona la barra espaciadora. Usa las flechas para elegir la posición y la barra espaciadora para soltarla; con Escape vuelve a su lugar.',
}

interface SortableListProps<T> {
  readonly items: readonly T[]
  readonly getId: (item: T) => string
  readonly getLabel: (item: T) => string
  readonly onReorder: (ids: readonly string[]) => void
  readonly renderItem: (item: T) => ReactNode
  readonly className?: string
  readonly itemClassName?: string
  /** El panel se ordena en rejilla; el menú, en una sola columna. */
  readonly shape?: 'list' | 'grid'
}

function crearAnuncios(
  ids: readonly string[],
  etiquetas: ReadonlyMap<string, string>,
): Announcements {
  const etiqueta = (id: UniqueIdentifier) => etiquetas.get(String(id)) ?? String(id)
  const posicion = (id: UniqueIdentifier) => ids.indexOf(String(id)) + 1
  const total = ids.length

  return {
    onDragStart: ({ active }) =>
      `Se levantó ${etiqueta(active.id)}. Muévelo con las flechas y suéltalo con la barra espaciadora; con Escape vuelve a su lugar.`,
    onDragOver: ({ active, over }) =>
      over === null
        ? undefined
        : `${etiqueta(active.id)} va por la posición ${String(posicion(over.id))} de ${String(total)}.`,
    onDragEnd: ({ active, over }) =>
      over === null
        ? `${etiqueta(active.id)} volvió a su lugar.`
        : `${etiqueta(active.id)} quedó en la posición ${String(posicion(over.id))} de ${String(total)}.`,
    onDragCancel: ({ active }) => `Se canceló el movimiento de ${etiqueta(active.id)}.`,
  }
}

/**
 * Una lista que se reordena arrastrando o con botones.
 *
 * El arrastre es accesible por teclado y cada paso se anuncia en español por
 * una region aria-live. Los botones de subir y bajar son la alternativa de un
 * solo puntero y comparten el mismo anuncio. El componente no sabe que ordena:
 * recibe los elementos y devuelve el orden nuevo.
 */
export default function SortableList<T>({
  items,
  getId,
  getLabel,
  onReorder,
  renderItem,
  className,
  itemClassName,
  shape = 'list',
}: SortableListProps<T>) {
  const [anuncio, setAnuncio] = useState('')
  const ids = items.map(getId)
  const etiquetas = new Map(items.map((item) => [getId(item), getLabel(item)]))
  const total = items.length

  const sensores = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: ACTIVACION_PX } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  )

  const mover = (desde: number, hasta: number) => {
    if (hasta < 0 || hasta >= total) {
      return
    }
    const texto = `${getLabel(items[desde])} quedó en la posición ${String(hasta + 1)} de ${String(total)}.`
    // Repetir el mismo texto no vuelve a disparar la region: un espacio duro
    // invisible alterna el contenido sin cambiar lo que se lee.
    setAnuncio((previo) => (previo === texto ? `${texto}\u00A0` : texto))
    onReorder(arrayMove([...ids], desde, hasta))
  }

  const alSoltar = ({ active, over }: DragEndEvent) => {
    if (over === null || active.id === over.id) {
      return
    }
    const desde = ids.indexOf(String(active.id))
    const hasta = ids.indexOf(String(over.id))
    if (desde < 0 || hasta < 0) {
      return
    }
    onReorder(arrayMove([...ids], desde, hasta))
  }

  return (
    <DndContext
      sensors={sensores}
      collisionDetection={closestCenter}
      accessibility={{ announcements: crearAnuncios(ids, etiquetas), screenReaderInstructions: INSTRUCCIONES }}
      onDragEnd={alSoltar}
    >
      <SortableContext items={ids} strategy={shape === 'grid' ? rectSortingStrategy : verticalListSortingStrategy}>
        <ul className={className}>
          {items.map((item, index) => (
            <SortableListItem
              key={getId(item)}
              id={getId(item)}
              label={getLabel(item)}
              position={index}
              total={total}
              className={itemClassName}
              onMove={(delta) => {
                mover(index, index + delta)
              }}
            >
              {renderItem(item)}
            </SortableListItem>
          ))}
        </ul>
      </SortableContext>
      <p role="status" aria-live="polite" className="sr-only">
        {anuncio}
      </p>
    </DndContext>
  )
}
