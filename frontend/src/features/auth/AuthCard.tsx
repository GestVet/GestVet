import type { ReactNode } from 'react'

import { Card, CardContent, CardDescription, CardFooter, CardHeader } from '../../components/ui/card'

interface AuthCardProps {
  readonly title: string
  readonly description?: ReactNode
  readonly children: ReactNode
  /** Enlaces a las otras pantallas de acceso. */
  readonly footer?: ReactNode
  /** Lo que la cuenta permite hacer. En escritorio va a la izquierda. */
  readonly aside?: ReactNode
}

/**
 * El marco comun de las pantallas de acceso.
 *
 * El titulo es el `h1` de la pagina: cada una de estas pantallas es una ruta
 * propia y el lector de pantalla necesita saber donde cayo. Con panel, el
 * formulario va primero en el documento y el panel solo cambia de lugar a la
 * vista en pantallas anchas, asi el orden del teclado empieza por el
 * formulario.
 */
export default function AuthCard({ title, description, children, footer, aside }: AuthCardProps) {
  const tarjeta = (
    <Card className="w-full gap-6 py-6 shadow-sm">
      <CardHeader className="gap-2 px-6 sm:px-8">
        <h1 className="m-0 font-heading text-2xl leading-tight font-bold text-foreground sm:text-3xl">
          {title}
        </h1>
        {description === undefined ? null : (
          <CardDescription className="text-base leading-relaxed">{description}</CardDescription>
        )}
      </CardHeader>
      <CardContent className="px-6 sm:px-8">{children}</CardContent>
      {footer === undefined ? null : (
        <CardFooter className="justify-center px-6 py-4 text-sm sm:px-8">{footer}</CardFooter>
      )}
    </Card>
  )

  if (aside === undefined) {
    return <div className="mx-auto w-full max-w-md my-auto">{tarjeta}</div>
  }

  return (
    <div className="mx-auto grid w-full max-w-5xl gap-6 my-auto lg:grid-cols-[minmax(0,1fr)_32rem] lg:items-start lg:gap-10">
      <div className="mx-auto w-full max-w-lg lg:order-2 lg:max-w-none">{tarjeta}</div>
      <div className="mx-auto w-full max-w-lg lg:order-1 lg:max-w-none">{aside}</div>
    </div>
  )
}
