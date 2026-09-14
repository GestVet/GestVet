import CountryFlag from './CountryFlag'
import { type CodigoDePais, PAISES, paisPorIso } from './phoneCountries'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select'

interface CountryCodeSelectProps {
  readonly value: CodigoDePais
  readonly onChange: (iso: CodigoDePais) => void
  readonly invalid: boolean
  readonly describedBy?: string
}

/**
 * El código de país de un teléfono, con su bandera.
 *
 * Una lista nativa no puede dibujar banderas, así que usa la de Radix: se abre
 * con teclado, se busca escribiendo el nombre y el lector de pantalla la
 * anuncia como lista. Cerrada muestra solo bandera y código para no robarle
 * ancho al número.
 */
export default function CountryCodeSelect({
  value,
  onChange,
  invalid,
  describedBy,
}: CountryCodeSelectProps) {
  const elegido = paisPorIso(value)

  return (
    <Select
      value={value}
      onValueChange={(iso) => {
        onChange(paisPorIso(iso).iso)
      }}
    >
      <SelectTrigger
        aria-label={`Código de país: ${elegido.nombre} ${elegido.prefijo}`}
        aria-invalid={invalid}
        aria-describedby={describedBy}
        className="h-10! shrink-0 gap-2 rounded-r-none px-3"
      >
        <SelectValue>
          <CountryFlag iso={elegido.iso} />
          <span className="tabular-nums">{elegido.prefijo}</span>
        </SelectValue>
      </SelectTrigger>
      <SelectContent position="popper" align="start" className="max-h-72">
        {PAISES.map((pais) => (
          <SelectItem key={pais.iso} value={pais.iso} textValue={pais.nombre}>
            <CountryFlag iso={pais.iso} />
            {/* Ancho fijo para el nombre: así los códigos quedan en columna. */}
            <span className="w-28">{pais.nombre}</span>
            <span className="text-muted-foreground tabular-nums">{pais.prefijo}</span>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}
