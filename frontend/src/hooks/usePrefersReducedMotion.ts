import { useSyncExternalStore } from 'react'

const CONSULTA = '(prefers-reduced-motion: reduce)'

// Una sola lista por pestaña: `matchMedia` se consulta en cada render para
// comparar, y crear un objeto nuevo cada vez solo agrega trabajo.
let lista: MediaQueryList | null = null

function media(): MediaQueryList {
  lista ??= window.matchMedia(CONSULTA)
  return lista
}

function suscribir(alCambiar: () => void): () => void {
  const consulta = media()
  consulta.addEventListener('change', alCambiar)
  return () => {
    consulta.removeEventListener('change', alCambiar)
  }
}

function leer(): boolean {
  return media().matches
}

function enElServidor(): boolean {
  return false
}

/**
 * Si el sistema pide menos movimiento.
 *
 * Los arrastres ordenan con una transicion de posicion; con esta preferencia
 * activa, el elemento salta a su lugar nuevo sin animarse. El valor acompana
 * al sistema si la persona lo cambia con la pagina abierta.
 */
export function usePrefersReducedMotion(): boolean {
  return useSyncExternalStore(suscribir, leer, enElServidor)
}
