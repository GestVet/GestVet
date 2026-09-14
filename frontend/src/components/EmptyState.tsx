import type { ReactNode } from 'react'

import { Empty, EmptyDescription, EmptyHeader, EmptyTitle } from './ui/empty'

interface EmptyStateProps {
  readonly title: string
  readonly description?: ReactNode
  /** Lo que la persona puede hacer para que deje de estar vacio. */
  readonly children?: ReactNode
}

/** Lo que se ve donde todavia no hay nada, o mientras carga. */
export default function EmptyState({ title, description, children }: EmptyStateProps) {
  return (
    <Empty className="gap-3 rounded-xl border border-dashed p-6 md:p-8">
      <EmptyHeader>
        <EmptyTitle className="text-base">{title}</EmptyTitle>
        {description === undefined ? null : <EmptyDescription>{description}</EmptyDescription>}
      </EmptyHeader>
      {children}
    </Empty>
  )
}
