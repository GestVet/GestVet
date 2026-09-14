import { useState } from 'react'

import CountryCodeOptions from './CountryCodeOptions'
import CountryFlag from './CountryFlag'
import Icon from './Icon'
import {
  type CodigoDePais,
  PAISES,
  PAISES_FRECUENTES,
  paisPorIso,
  sinTildes,
} from './phoneCountries'
import { Button } from './ui/button'
import { Command, CommandEmpty, CommandInput, CommandList, CommandSeparator } from './ui/command'
import { Popover, PopoverContent, PopoverTrigger } from './ui/popover'

interface CountryCodeSelectProps {
  readonly value: CodigoDePais
  readonly onChange: (iso: CodigoDePais) => void
  readonly invalid: boolean
  readonly describedBy?: string
}

// Compara contra el nombre y el código, no contra el identificador interno:
// escribir "pe" encuentra Perú, y "51" o "+51" también.
function coincide(_valor: string, busqueda: string, palabras?: string[]): number {
  const buscado = sinTildes(busqueda)
  return palabras?.some((palabra) => sinTildes(palabra).includes(buscado)) === true ? 1 : 0
}

/**
 * El código de país de un teléfono, con su bandera y un buscador.
 *
 * Son 245 países, así que la lista se filtra escribiendo el nombre o el código.
 * Sin búsqueda muestra primero los frecuentes. Cerrada muestra solo bandera y
 * código para no robarle ancho al número.
 */
export default function CountryCodeSelect({
  value,
  onChange,
  invalid,
  describedBy,
}: CountryCodeSelectProps) {
  const [abierto, setAbierto] = useState(false)
  const [busqueda, setBusqueda] = useState('')
  const elegido = paisPorIso(value)
  const elegir = (iso: CodigoDePais) => {
    onChange(iso)
    setAbierto(false)
    setBusqueda('')
  }

  return (
    <Popover open={abierto} onOpenChange={setAbierto}>
      <PopoverTrigger asChild>
        <Button
          type="button"
          variant="outline"
          role="combobox"
          aria-expanded={abierto}
          aria-label={`Código de país: ${elegido.nombre} ${elegido.prefijo}`}
          aria-invalid={invalid}
          aria-describedby={describedBy}
          className="h-10 shrink-0 gap-2 rounded-r-none px-3 font-normal"
        >
          <CountryFlag iso={elegido.iso} />
          <span className="tabular-nums">{elegido.prefijo}</span>
          <Icon name="desplegar" size={14} />
        </Button>
      </PopoverTrigger>
      <PopoverContent align="start" className="w-80 p-0">
        <Command filter={coincide}>
          <CommandInput
            placeholder="Busca un país o código"
            value={busqueda}
            onValueChange={setBusqueda}
          />
          <CommandList className="max-h-72">
            <CommandEmpty>No hay un país con ese nombre o código.</CommandEmpty>
            {busqueda === '' ? (
              <>
                <CountryCodeOptions
                  titulo="Frecuentes"
                  grupo="frecuentes"
                  paises={PAISES_FRECUENTES}
                  elegido={elegido.iso}
                  onElegir={elegir}
                />
                <CommandSeparator />
              </>
            ) : null}
            <CountryCodeOptions
              titulo="Todos los países"
              grupo="todos"
              paises={PAISES}
              elegido={elegido.iso}
              onElegir={elegir}
            />
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  )
}
