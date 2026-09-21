import { cn } from 'cn'

interface SortableSkeletonProps {
  /** Cuantas filas o tarjetas reserva. Se usa el mismo numero que tendra la lista. */
  readonly rows: number
  readonly shape?: 'list' | 'grid'
}

const LISTA = 'm-0 flex list-none flex-col gap-1 p-0'
const REJILLA = 'm-0 grid list-none gap-4 p-0 sm:grid-cols-2 lg:grid-cols-3'

/**
 * El hueco de la lista reordenable mientras llega su fragmento.
 *
 * @dnd-kit viaja en el fragmento que se descarga al entrar en modo edicion,
 * asi que la primera vez hay un instante sin controles. El esqueleto reserva
 * la misma forma que tendra la lista para que nada salte de lugar; es decorativo
 * y se oculta a los lectores de pantalla.
 */
export default function SortableSkeleton({ rows, shape = 'list' }: SortableSkeletonProps) {
  const enRejilla = shape === 'grid'

  return (
    <ul aria-hidden="true" className={cn(enRejilla ? REJILLA : LISTA)}>
      {Array.from({ length: rows }, (_, indice) => (
        <li
          key={indice}
          className={cn(
            'animate-pulse bg-muted motion-reduce:animate-none',
            enRejilla ? 'h-36 rounded-xl' : 'h-10 rounded-lg',
          )}
        />
      ))}
    </ul>
  )
}
