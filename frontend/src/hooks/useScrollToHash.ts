import { useEffect } from 'react'
import { useLocation } from 'react-router'

/**
 * Lleva la vista a la seccion que nombra el ancla de la direccion.
 *
 * El enrutador cambia la URL sin recargar, asi que el navegador no hace el
 * salto que haria con un enlace comun: "Cómo reservar" cambiaba la direccion
 * y la pagina se quedaba arriba. Depende tambien de la clave de la ubicacion
 * para que volver a pulsar el mismo enlace vuelva a llevar a la seccion.
 */
export function useScrollToHash(): void {
  const { hash, key } = useLocation()

  useEffect(() => {
    if (hash === '') {
      return
    }
    document.getElementById(decodeURIComponent(hash.slice(1)))?.scrollIntoView()
  }, [hash, key])
}
