import { useEffect, useState } from 'react'

const CADA_MINUTO_MS = 60_000

/**
 * La hora actual, que se renueva sola cada minuto.
 *
 * Para las acciones que se habilitan a una hora dada: sin renovarse, una
 * pantalla abierta desde antes seguiría ofreciéndolas deshabilitadas.
 */
export function useNow(): number {
  const [ahora, setAhora] = useState(() => Date.now())

  useEffect(() => {
    const reloj = window.setInterval(() => {
      setAhora(Date.now())
    }, CADA_MINUTO_MS)
    return () => {
      window.clearInterval(reloj)
    }
  }, [])

  return ahora
}
