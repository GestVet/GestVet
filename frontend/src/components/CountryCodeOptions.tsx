import CountryFlag from './CountryFlag'
import { type CodigoDePais, type PaisTelefonico, sinTildes } from './phoneCountries'
import { CommandGroup, CommandItem } from './ui/command'

interface CountryCodeOptionsProps {
  readonly titulo: string
  /** Distingue a Perú en "Frecuentes" de Perú en "Todos los países". */
  readonly grupo: string
  readonly paises: readonly PaisTelefonico[]
  readonly elegido: CodigoDePais
  readonly onElegir: (iso: CodigoDePais) => void
}

/** Un grupo de países del selector de código telefónico. */
export default function CountryCodeOptions({
  titulo,
  grupo,
  paises,
  elegido,
  onElegir,
}: CountryCodeOptionsProps) {
  return (
    <CommandGroup heading={titulo}>
      {paises.map((pais) => (
        <CommandItem
          key={pais.iso}
          value={`${grupo}-${pais.iso}`}
          keywords={[pais.nombre, sinTildes(pais.nombre), pais.prefijo]}
          data-checked={pais.iso === elegido}
          onSelect={() => {
            onElegir(pais.iso)
          }}
        >
          <CountryFlag iso={pais.iso} />
          <span className="flex-1 truncate">{pais.nombre}</span>
          <span className="text-muted-foreground tabular-nums">{pais.prefijo}</span>
        </CommandItem>
      ))}
    </CommandGroup>
  )
}
