import { useState } from 'react'

import type { SpecialtyResponse, UserResponse } from '../../api/types'
import { Button } from '../../components/ui/button'
import SpecialtyBadges from './SpecialtyBadges'
import StaffSpecialtiesDialog from './StaffSpecialtiesDialog'

interface StaffSpecialtiesProps {
  readonly account: UserResponse
  readonly assigned: readonly SpecialtyResponse[]
  /** Solo quien administra personal puede reasignarlas. */
  readonly editable: boolean
}

/**
 * Las especialidades de un veterinario, con las que aparece al reservar.
 *
 * Se editan en una ventana aparte y no en línea: el catálogo agrupado por
 * categoría no entra en una celda de la tabla.
 */
export default function StaffSpecialties({ account, assigned, editable }: StaffSpecialtiesProps) {
  const [editando, setEditando] = useState(false)

  return (
    <div className="flex max-w-xs flex-col items-start gap-1 whitespace-normal">
      <SpecialtyBadges specialties={assigned} />
      {editable ? (
        <Button
          type="button"
          size="sm"
          variant="ghost"
          onClick={() => {
            setEditando(true)
          }}
        >
          Editar
        </Button>
      ) : null}
      {editando ? (
        <StaffSpecialtiesDialog
          account={account}
          initial={assigned.map((especialidad) => especialidad.id)}
          onClose={() => {
            setEditando(false)
          }}
        />
      ) : null}
    </div>
  )
}
