import { useState } from 'react'

import Icon from '../../components/Icon'
import { Button } from '../../components/ui/button'
import { Sheet, SheetContent, SheetTitle, SheetTrigger } from '../../components/ui/sheet'
import type { NavEntry } from './navigation'
import NavList from './NavList'
import SessionActions from './SessionActions'

interface MobileMenuProps {
  readonly entries: readonly NavEntry[]
  readonly firstName: string
}

/**
 * El menu en pantallas angostas.
 *
 * Un administrador tiene nueve entradas: en fila ocupaban un tercio de la
 * pantalla del celular antes de llegar al contenido. Aca quedan detras de un
 * boton, y el panel se cierra al elegir una pantalla.
 */
export default function MobileMenu({ entries, firstName }: MobileMenuProps) {
  const [open, setOpen] = useState(false)
  const close = () => {
    setOpen(false)
  }

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button type="button" variant="ghost" size="icon-lg" className="size-11" aria-label="Abrir menú">
          <Icon name="menu" size={22} />
        </Button>
      </SheetTrigger>
      <SheetContent side="left" className="w-72 gap-4 p-4">
        <SheetTitle className="m-0 px-3 pt-2 font-heading text-lg font-semibold text-primary">
          Menú
        </SheetTitle>
        <nav aria-label="Navegación principal" className="flex-1 overflow-y-auto">
          <NavList entries={entries} onNavigate={close} />
        </nav>
        <SessionActions firstName={firstName} onNavigate={close} />
      </SheetContent>
    </Sheet>
  )
}
