import { Fragment, useState } from 'react'

import type { PetResponse } from '../../api/types'
import StatusBadge from '../../components/StatusBadge'
import PetHistory from './PetHistory'

interface PetRowProps {
  readonly mascota: PetResponse
  readonly dandoDeBaja: boolean
  readonly onDarDeBaja: () => void
}

export default function PetRow({ mascota, dandoDeBaja, onDarDeBaja }: PetRowProps) {
  const [expandido, setExpandido] = useState(false)

  return (
    <Fragment>
      <tr>
        <td>{mascota.name}</td>
        <td>{mascota.species}</td>
        <td>{mascota.breed}</td>
        <td>{mascota.age_in_years} años</td>
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
          {mascota.is_active ? (
            <button type="button" className="btn btn-plain" disabled={dandoDeBaja} onClick={onDarDeBaja}>
              Registrar fallecimiento
            </button>
          ) : (
            <span className="muted">
              Si fue un error, pedile al personal de la clínica que lo corrija.
            </span>
          )}
        </td>
      </tr>
      {expandido ? (
        <tr>
          <td colSpan={6}>
            <PetHistory petId={mascota.id} />
          </td>
        </tr>
      ) : null}
    </Fragment>
  )
}
