import { Fragment, useState } from 'react'

import type { PetResponse } from '../../api/types'
import StatusBadge from '../../components/StatusBadge'
import ClientPetHistory from './ClientPetHistory'

interface ClientPetRowProps {
  readonly mascota: PetResponse
  readonly corrigiendo: boolean
  readonly onCorregir: () => void
}

export default function ClientPetRow({ mascota, corrigiendo, onCorregir }: ClientPetRowProps) {
  const [expandido, setExpandido] = useState(false)

  return (
    <Fragment>
      <tr>
        <td>{mascota.name}</td>
        <td>{mascota.species}</td>
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
            {expandido ? 'Ocultar historia' : 'Ver historia clínica'}
          </button>
          <button type="button" className="btn btn-plain" disabled={corrigiendo} onClick={onCorregir}>
            Corregir a {mascota.is_active ? 'fallecida' : 'activa'}
          </button>
        </td>
      </tr>
      {expandido ? (
        <tr>
          <td colSpan={4}>
            <ClientPetHistory petId={mascota.id} />
          </td>
        </tr>
      ) : null}
    </Fragment>
  )
}
