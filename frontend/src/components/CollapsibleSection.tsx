import { type ReactNode, useId, useState } from 'react'

import CollapsibleHeading from './CollapsibleHeading'

interface CollapsibleSectionProps {
  readonly title: string
  readonly as?: 'h2' | 'h3' | 'h4'
  readonly description?: ReactNode
  /** Botones a la derecha del título; siguen a mano con la sección cerrada. */
  readonly actions?: ReactNode
  readonly defaultOpen?: boolean
  readonly children: ReactNode
}

/**
 * Una parte de una pantalla que se abre y cierra tocando su título.
 *
 * Sirve para lo que se consulta de vez en cuando, como un formulario de
 * edición o las internaciones: la pantalla muestra primero lo importante y no
 * se estira con el resto. Cerrada, el contenido sigue montado, así que
 * un formulario a medio llenar no se pierde.
 */
export default function CollapsibleSection({
  title,
  as = 'h3',
  description,
  actions,
  defaultOpen = true,
  children,
}: CollapsibleSectionProps) {
  const [abierto, setAbierto] = useState(defaultOpen)
  const contenidoId = useId()

  return (
    <section className="flex flex-col gap-3">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <CollapsibleHeading
          title={title}
          as={as}
          description={description}
          open={abierto}
          controls={contenidoId}
          onToggle={() => {
            setAbierto((valor) => !valor)
          }}
        />
        {actions === undefined ? null : (
          <div className="flex flex-wrap items-start gap-2">{actions}</div>
        )}
      </div>
      <div id={contenidoId} hidden={!abierto} className="flex flex-col gap-3">
        {children}
      </div>
    </section>
  )
}
