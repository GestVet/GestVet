import type { ReactNode } from 'react'

interface DialogFormActionsProps {
  readonly children: ReactNode
}

/**
 * Los botones al pie de un formulario en ventana.
 *
 * En el celular se apilan a lo ancho con la acción principal arriba, al
 * alcance del pulgar; desde tablet quedan a la derecha, con la principal al
 * final. Por eso cada formulario pone primero "Cancelar" y después la acción.
 */
export default function DialogFormActions({ children }: DialogFormActionsProps) {
  return (
    <div className="flex flex-col-reverse gap-2 pt-1 sm:flex-row sm:justify-end">{children}</div>
  )
}
