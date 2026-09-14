import { BANDERAS } from './countryFlags'
import type { CodigoDePais } from './phoneCountries'

interface CountryFlagProps {
  readonly iso: CodigoDePais
}

/** La bandera de un país. Decorativa: el nombre o el código ya están escritos al lado. */
export default function CountryFlag({ iso }: CountryFlagProps) {
  const Bandera = BANDERAS[iso]
  return (
    <Bandera
      aria-hidden="true"
      className="h-3.5 w-5 shrink-0 rounded-xs shadow-xs ring-1 ring-foreground/10"
    />
  )
}
