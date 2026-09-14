import { useState } from 'react'

import Icon from './Icon'
import { buttonVariants } from './ui/button'

// RENIAN no acepta el número en la dirección: se abre su buscador y el número
// queda copiado para pegarlo.
const RENIAN_CONSULTA = 'https://www.renian.pe/consulta'

interface MicrochipLookupProps {
  readonly numero: string
}

/** El número de microchip con un atajo para buscarlo en RENIAN. */
export default function MicrochipLookup({ numero }: MicrochipLookupProps) {
  const [copiado, setCopiado] = useState(false)

  return (
    <span className="flex flex-wrap items-center gap-2">
      <span className="tabular-nums">{numero}</span>
      <a
        href={RENIAN_CONSULTA}
        target="_blank"
        rel="noopener noreferrer"
        className={buttonVariants({ variant: 'outline', size: 'sm' })}
        onClick={() => {
          navigator.clipboard
            .writeText(numero)
            .then(() => {
              setCopiado(true)
            })
            .catch(() => {
              setCopiado(false)
            })
        }}
      >
        <Icon name="buscar" size={14} />
        <span>Consultar en RENIAN</span>
        <span className="sr-only">(se abre en otra pestaña)</span>
      </a>
      <span className="text-xs font-normal text-muted-foreground" aria-live="polite">
        {copiado ? 'Número copiado: pégalo en el buscador de RENIAN.' : ''}
      </span>
    </span>
  )
}
