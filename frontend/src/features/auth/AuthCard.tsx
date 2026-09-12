import type { ReactNode } from 'react'

import { Card, CardContent, CardDescription, CardFooter, CardHeader } from '../../components/ui/card'

interface AuthCardProps {
  readonly title: string
  readonly description?: ReactNode
  readonly children: ReactNode
  /** Enlaces a las otras pantallas de acceso. */
  readonly footer?: ReactNode
}

/**
 * El marco comun de las pantallas de acceso.
 *
 * El titulo es el `h1` de la pagina: cada una de estas pantallas es una ruta
 * propia y el lector de pantalla necesita saber donde cayo.
 */
export default function AuthCard({ title, description, children, footer }: AuthCardProps) {
  return (
    <Card className="mx-auto w-full max-w-md gap-6 py-6 shadow-sm sm:mt-4">
      <CardHeader className="gap-2 px-6">
        <h1 className="m-0 font-heading text-2xl leading-tight font-semibold text-primary">
          {title}
        </h1>
        {description === undefined ? null : (
          <CardDescription className="text-base">{description}</CardDescription>
        )}
      </CardHeader>
      <CardContent className="px-6">{children}</CardContent>
      {footer === undefined ? null : (
        <CardFooter className="justify-center px-6 py-4 text-sm">{footer}</CardFooter>
      )}
    </Card>
  )
}
