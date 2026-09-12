import { Fragment, useState } from 'react'

import type { PetResponse } from '../../api/types'
import PetProfilePanel from '../../components/PetProfilePanel'
import StatusBadge from '../../components/StatusBadge'
import { useIsVeterinarian } from '../../store/session'
import ClientPetHistory from './ClientPetHistory'
import ClientPetHospitalizations from './ClientPetHospitalizations'

interface ClientPetRowProps {
  readonly mascota: PetResponse
  readonly corrigiendo: boolean
  readonly onCorregir: () => void
}

export default function ClientPetRow({ mascota, corrigiendo, onCorregir }: ClientPetRowProps) {
  const [expandido, setExpandido] = useState(false)
  const esVeterinario = useIsVeterinarian()

  return (
    <Fragment>
      <tr>
        <td>{mascota.name}</td>
        <td>{mascota.species}</td>
        <td>{mascota.weight_kg ? `${mascota.weight_kg} kg` : '—'}</td>
        <td>{mascota.height_cm ? `${mascota.height_cm} cm` : '—'}</td>
        <td>
          <StatusBadge
            label={mascota.is_active ? 'Activa' : 'Fallecida'}
            tone={mascota.is_active ? 'completed' : undefined}
          />
        </td>
        <td className="row-actions">
          <button
            type="button"
            className="btn btn-plain"
            onClick={() => {
              setExpandido(!expandido)
            }}
          >
            {expandido ? 'Ocultar detalles' : 'Ver más detalles'}
          </button>
          <button
            type="button"
            className="btn btn-plain"
            disabled={corrigiendo}
            onClick={onCorregir}
          >
            Corregir a {mascota.is_active ? 'fallecida' : 'activa'}
          </button>
        </td>
      </tr>
      {expandido ? (
        <tr>
          <td colSpan={6}>
            <div className="stack">
              <PetProfilePanel
                mascota={mascota}
                canEditOwnerFields={false}
                canEditClinicalFields={esVeterinario}
              />
              <ClientPetHistory petId={mascota.id} />
              <ClientPetHospitalizations petId={mascota.id} />
            </div>
          </td>
        </tr>
      ) : null}
    </Fragment>
  )
}
