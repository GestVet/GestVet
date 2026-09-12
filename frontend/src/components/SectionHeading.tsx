import type { ReactNode } from 'react'

interface SectionHeadingProps {
  readonly children: ReactNode
  /** El nivel lo decide quien la usa, segun donde cae en la pagina. */
  readonly as?: 'h2' | 'h3'
  readonly description?: ReactNode
}

/** El titulo de una seccion dentro de una pantalla. */
export default function SectionHeading({ children, as = 'h2', description }: SectionHeadingProps) {
  const Heading = as
  return (
    <div className="flex flex-col gap-1">
      <Heading className="m-0 font-heading text-lg leading-snug font-semibold text-foreground">
        {children}
      </Heading>
      {description === undefined ? null : (
        <p className="m-0 text-sm text-muted-foreground">{description}</p>
      )}
    </div>
  )
}
