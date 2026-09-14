import { cn } from 'cn'
import { type ReactNode, useId, useState } from 'react'

import CollapsibleHeading from './CollapsibleHeading'
import SectionHeading from './SectionHeading'
import { Card, CardContent, CardHeader } from './ui/card'

interface SectionCardProps {
  readonly title: string
  readonly description?: ReactNode
  /** Botones de la seccion, a la derecha del titulo. */
  readonly actions?: ReactNode
  readonly children: ReactNode
  readonly as?: 'h2' | 'h3'
  /** Se abre y cierra tocando el titulo. */
  readonly collapsible?: boolean
  readonly defaultOpen?: boolean
  /**
   * Un contenido largo se desplaza dentro de la tarjeta, con la rueda, el dedo
   * o el teclado, en vez de estirar la pagina.
   */
  readonly scrollable?: boolean
}

// Enfocable y con nombre: quien usa teclado tambien puede desplazar el contenido.
function propsDeDesplazamiento(scrollable: boolean, title: string) {
  if (!scrollable) {
    return { className: 'flex flex-col gap-4 px-5' }
  }
  return {
    tabIndex: 0,
    role: 'region',
    'aria-label': title,
    className: cn(
      'flex flex-col gap-4 px-5',
      'max-h-[min(34rem,70dvh)] overflow-y-auto overscroll-contain outline-none focus-visible:ring-3 focus-visible:ring-ring/50',
    ),
  }
}

/** Un bloque de una pantalla: titulo, descripcion y contenido en una tarjeta. */
export default function SectionCard({
  title,
  description,
  actions,
  children,
  as = 'h2',
  collapsible = false,
  defaultOpen = true,
  scrollable = false,
}: SectionCardProps) {
  const [abierto, setAbierto] = useState(defaultOpen)
  const contenidoId = useId()

  return (
    <Card className="gap-4 py-5 shadow-sm">
      <CardHeader className="flex flex-wrap items-start justify-between gap-3 px-5">
        {collapsible ? (
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
        ) : (
          <SectionHeading as={as} description={description}>
            {title}
          </SectionHeading>
        )}
        {actions === undefined ? null : <div className="flex flex-wrap gap-2">{actions}</div>}
      </CardHeader>
      <CardContent
        id={contenidoId}
        hidden={collapsible && !abierto}
        {...propsDeDesplazamiento(scrollable, title)}
      >
        {children}
      </CardContent>
    </Card>
  )
}
