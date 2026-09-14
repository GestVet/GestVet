import type { Coincidencias, NombreDelCatalogo } from '../../services/catalogName'

interface SimilarNamesProps {
  readonly coincidencias: Coincidencias<NombreDelCatalogo>
}

function etiqueta(entrada: NombreDelCatalogo): string {
  return entrada.is_active ? entrada.name : `${entrada.name} (desactivada)`
}

/**
 * Lo ya cargado que se parece a lo que se escribe.
 *
 * Avisa antes de guardar: un nombre igual no entraría, y uno parecido puede ser
 * la misma raza escrita de otra forma ("Pit bull" y "Pitbull") o un sinónimo
 * que conviene revisar a ojo. Se anuncia al lector de pantalla a medida que
 * cambia.
 */
export default function SimilarNames({ coincidencias }: SimilarNamesProps) {
  const { exacto, parecidos } = coincidencias

  return (
    <div aria-live="polite" className="flex flex-col gap-2 text-sm">
      {exacto === undefined ? null : (
        <p className="font-medium text-destructive">
          Ya existe «{exacto.name}».
          {exacto.is_active ? '' : ' Está desactivada: actívala en vez de agregarla de nuevo.'}
        </p>
      )}
      {parecidos.length === 0 ? null : (
        <div className="flex flex-col gap-1.5">
          <p className="text-muted-foreground">Parecidos ya cargados. Revisa que no sea uno de estos:</p>
          <ul className="flex flex-wrap gap-1.5">
            {parecidos.map((parecido) => (
              <li key={parecido.name} className="rounded-md border bg-muted px-2 py-0.5 text-foreground">
                {etiqueta(parecido)}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
