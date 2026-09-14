import { cn } from 'cn'
import type { ReactNode } from 'react'

import Icon from './Icon'
import type { IconName } from './icons'

interface FieldIconProps {
  /** Sin icono, el campo se muestra tal cual. */
  readonly icon: IconName | undefined
  /** En un texto largo el icono va arriba, a la altura de la primera línea. */
  readonly multiline?: boolean
  readonly children: ReactNode
}

/**
 * Pone un icono a la izquierda de un campo.
 *
 * El icono acompaña a la etiqueta, que es la que nombra el campo: queda oculto
 * para el lector de pantalla y deja pasar los clics, así tocarlo enfoca el campo
 * igual. El relleno del campo se corre desde acá, sin que cada campo lo sepa.
 */
export default function FieldIcon({ icon, multiline = false, children }: FieldIconProps) {
  return (
    <div
      className={cn(
        'relative',
        icon !== undefined && '[&_input]:pl-9 [&_select]:pl-9 [&_textarea]:pl-9',
      )}
    >
      {children}
      {icon === undefined ? null : (
        <Icon
          name={icon}
          size={16}
          className={cn(
            'pointer-events-none absolute left-3 text-muted-foreground',
            multiline ? 'top-3' : 'top-1/2 -translate-y-1/2',
          )}
        />
      )}
    </div>
  )
}
