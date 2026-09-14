import { useMemo, useState } from 'react'

/**
 * Parte una lista en páginas.
 *
 * Sin tamaño, devuelve la lista entera en una sola página. Si la lista se
 * achica (un filtro nuevo), la página actual se acomoda a la última que exista
 * en vez de quedar vacía.
 */
export function usePagination<T>(items: readonly T[], pageSize: number | undefined) {
  const [pagina, setPagina] = useState(0)
  const tamanio = pageSize ?? Math.max(items.length, 1)
  const total = Math.max(1, Math.ceil(items.length / tamanio))
  const actual = Math.min(pagina, total - 1)
  const visibles = useMemo(
    () => items.slice(actual * tamanio, (actual + 1) * tamanio),
    [items, actual, tamanio],
  )

  return { visibles, actual, total, irA: setPagina }
}
