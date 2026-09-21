import { cn } from 'cn'
import type { ReactNode } from 'react'
import { Link } from 'react-router'

import Icon from '../../components/Icon'
import type { Acceso } from './dashboardAccesos'

interface DashboardAccesoCardProps {
  readonly acceso: Acceso
  /** En modo edición la tarjeta no navega: es contenido que se ordena. */
  readonly estatica?: boolean
  readonly oculto?: boolean
  /** Control propio de la edición, como el ojo que la oculta o la muestra. */
  readonly accion?: ReactNode
}

const TARJETA =
  'relative flex h-full flex-col gap-2 rounded-xl bg-card p-5 text-card-foreground shadow-sm ring-1 ring-foreground/10'

/**
 * Una tarjeta de acceso del panel.
 *
 * Es la misma en los dos modos: como enlace en el panel normal y como
 * contenido fijo mientras se personaliza, para que tocar o arrastrar no
 * abra una pantalla sin querer.
 */
export default function DashboardAccesoCard({
  acceso,
  estatica = false,
  oculto = false,
  accion,
}: DashboardAccesoCardProps) {
  const cuerpo = (
    <>
      {accion === undefined ? null : <div className="absolute top-3 right-3">{accion}</div>}
      <Icon className="text-primary" name={acceso.icon} size={28} />
      <h2 className="m-0 font-heading text-lg font-semibold text-primary">{acceso.title}</h2>
      <p className="m-0 text-sm leading-relaxed text-muted-foreground">{acceso.description}</p>
    </>
  )
  const clases = cn(TARJETA, oculto && 'opacity-60')

  if (estatica) {
    return <div className={clases}>{cuerpo}</div>
  }

  return (
    <Link
      to={acceso.to}
      className={cn(
        clases,
        'outline-none transition-shadow hover:shadow-md focus-visible:ring-3 focus-visible:ring-ring/50 motion-reduce:transition-none',
      )}
    >
      {cuerpo}
    </Link>
  )
}
