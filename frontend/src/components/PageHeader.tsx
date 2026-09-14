import type { ReactNode } from 'react'

interface PageHeaderProps {
  readonly title: string
  readonly description?: ReactNode
  /** Botones de la pantalla. En el celular bajan debajo del titulo. */
  readonly actions?: ReactNode
}

/** El titulo de cada pantalla, que es su unico `h1`. */
export default function PageHeader({ title, description, actions }: PageHeaderProps) {
  return (
    <header className="flex flex-wrap items-end justify-between gap-4">
      <div className="flex min-w-0 flex-col gap-1">
        <h1 className="m-0 font-heading text-2xl leading-tight font-bold text-primary sm:text-3xl">
          {title}
        </h1>
        {description === undefined ? null : (
          <p className="m-0 text-base text-muted-foreground">{description}</p>
        )}
      </div>
      {actions === undefined ? null : <div className="flex flex-wrap gap-2">{actions}</div>}
    </header>
  )
}
