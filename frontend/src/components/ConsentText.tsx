import FormMessage from './FormMessage'

/** Lo que hace falta de un texto de consentimiento para mostrarlo. */
export interface ConsentTextContent {
  readonly title: string
  /** Sin versión, el texto es la copia firmada de un pedido: su versión no se muestra. */
  readonly version?: number
  readonly body: string
}

interface ConsentTextProps {
  readonly id: string
  readonly template: ConsentTextContent | undefined
  readonly isError: boolean
}

/**
 * El texto de un consentimiento, tal como queda copiado en la firma.
 *
 * Va en una caja con desplazamiento propio para que el formulario no se
 * vuelva interminable en el celular. La caja toma el foco para que se pueda
 * recorrer con el teclado, y la versión queda a la vista porque es la que
 * se firma.
 */
export default function ConsentText({ id, template, isError }: ConsentTextProps) {
  if (isError) {
    return (
      <FormMessage tone="error">
        No se pudo cargar el texto del consentimiento. Vuelve a intentarlo en unos segundos.
      </FormMessage>
    )
  }
  if (template === undefined) {
    return <p className="m-0 text-sm text-muted-foreground">Cargando el texto del consentimiento…</p>
  }

  const idTitulo = `${id}-titulo`

  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
        <h3 id={idTitulo} className="m-0 text-sm leading-snug font-semibold text-foreground">
          {template.title}
        </h3>
        {template.version === undefined ? null : (
          <span className="text-xs text-muted-foreground">Versión {template.version}</span>
        )}
      </div>
      <div
        id={id}
        tabIndex={0}
        role="region"
        aria-labelledby={idTitulo}
        className="max-h-56 overflow-y-auto rounded-lg border border-input bg-muted/40 px-3 py-2.5 text-sm leading-relaxed whitespace-pre-line text-foreground outline-none focus-visible:ring-3 focus-visible:ring-ring/50"
      >
        {template.body}
      </div>
    </div>
  )
}
