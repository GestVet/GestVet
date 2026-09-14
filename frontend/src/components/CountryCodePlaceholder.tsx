import type { CodigoDePais } from './phoneCountries'
import { paisPorIso } from './phoneCountries'
import { Button } from './ui/button'

interface CountryCodePlaceholderProps {
  readonly iso: CodigoDePais
}

/** Lo que se ve mientras llegan las banderas: el código, todavía sin poder cambiarlo. */
export default function CountryCodePlaceholder({ iso }: CountryCodePlaceholderProps) {
  return (
    <Button
      type="button"
      variant="outline"
      disabled
      className="h-10 shrink-0 rounded-r-none px-3 font-normal tabular-nums"
    >
      {paisPorIso(iso).prefijo}
    </Button>
  )
}
