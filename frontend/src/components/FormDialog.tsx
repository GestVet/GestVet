import { type ReactNode, useRef } from 'react'

import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from './ui/dialog'

interface FormDialogProps {
  readonly open: boolean
  readonly onOpenChange: (open: boolean) => void
  readonly title: string
  readonly description?: ReactNode
  /** `lg` para formularios de dos columnas o con listas largas, como los permisos. */
  readonly size?: 'md' | 'lg'
  readonly children: ReactNode
}

const ANCHOS = { md: 'sm:max-w-lg', lg: 'sm:max-w-2xl' } as const

/**
 * Un formulario en una ventana sobre la pantalla.
 *
 * Deja la pantalla para lo que se consulta, la tabla o el cuadro, y trae el
 * formulario solo cuando alguien va a cargar algo. La primitiva de Radix
 * encierra el foco adentro y cierra con Escape. Un formulario largo se
 * desplaza dentro de la ventana, también en el celular.
 */
export default function FormDialog({
  open,
  onOpenChange,
  title,
  description,
  size = 'md',
  children,
}: FormDialogProps) {
  // La ventana se abre desde estado y no desde su propio disparador, así que
  // Radix no sabe a dónde devolver el foco. Se recuerda lo que lo tenía al
  // abrir: quien usa teclado vuelve al botón que la abrió y no al inicio.
  const retorno = useRef<HTMLElement | null>(null)
  // Sin descripción, Radix pide decirlo explícitamente para no anunciar un vacío.
  const sinDescripcion = description === undefined ? { 'aria-describedby': undefined } : {}

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        {...sinDescripcion}
        className={`max-h-[calc(100dvh-2rem)] gap-5 overflow-y-auto p-5 sm:p-6 ${ANCHOS[size]}`}
        onOpenAutoFocus={() => {
          retorno.current = document.activeElement instanceof HTMLElement ? document.activeElement : null
        }}
        onCloseAutoFocus={(evento) => {
          if (retorno.current?.isConnected === true) {
            evento.preventDefault()
            retorno.current.focus()
          }
        }}
      >
        <DialogHeader className="gap-1.5 pr-8">
          <DialogTitle className="text-lg leading-tight font-semibold">{title}</DialogTitle>
          {description === undefined ? null : <DialogDescription>{description}</DialogDescription>}
        </DialogHeader>
        {children}
      </DialogContent>
    </Dialog>
  )
}
