import type { PetResponse } from '../../api/types'
import RowExpandButton from '../../components/RowExpandButton'
import CorrectPetStatusDialog from './CorrectPetStatusDialog'

interface ClientPetActionsProps {
  readonly mascota: PetResponse
  readonly isExpanded: boolean
  readonly onToggle: () => void
}

export default function ClientPetActions({ mascota, isExpanded, onToggle }: ClientPetActionsProps) {
  return (
    <div className="flex flex-wrap gap-2">
      <RowExpandButton
        isExpanded={isExpanded}
        onToggle={onToggle}
        collapsedLabel="Ver más detalles"
        expandedLabel="Ocultar detalles"
      />
      <CorrectPetStatusDialog mascota={mascota} />
    </div>
  )
}
