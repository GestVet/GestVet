import type { ReactNode } from 'react'

import SectionHeading from './SectionHeading'
import { Card, CardContent, CardHeader } from './ui/card'

interface SectionCardProps {
  readonly title: string
  readonly description?: ReactNode
  /** Botones de la seccion, a la derecha del titulo. */
  readonly actions?: ReactNode
  readonly children: ReactNode
  readonly as?: 'h2' | 'h3'
}

/** Un bloque de una pantalla: titulo, descripcion y contenido en una tarjeta. */
export default function SectionCard({
  title,
  description,
  actions,
  children,
  as = 'h2',
}: SectionCardProps) {
  return (
    <Card className="gap-4 py-5 shadow-sm">
      <CardHeader className="flex flex-wrap items-start justify-between gap-3 px-5">
        <SectionHeading as={as} description={description}>
          {title}
        </SectionHeading>
        {actions === undefined ? null : <div className="flex flex-wrap gap-2">{actions}</div>}
      </CardHeader>
      <CardContent className="flex flex-col gap-4 px-5">{children}</CardContent>
    </Card>
  )
}
