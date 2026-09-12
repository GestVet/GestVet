import { Fragment } from 'react'

import type { UserResponse } from '../../api/types'
import Icon from '../../components/Icon'
import StatusBadge from '../../components/StatusBadge'
import ClientPets from './ClientPets'

interface ClientRowProps {
  readonly cliente: UserResponse
  readonly expandido: boolean
  readonly onToggle: () => void
  readonly puedeActivar: boolean
  readonly cambiandoEstado: boolean
  readonly onCambiarEstado: () => void
}

export default function ClientRow({
  cliente,
  expandido,
  onToggle,
  puedeActivar,
  cambiandoEstado,
  onCambiarEstado,
}: ClientRowProps) {
  return (
    <Fragment>
      <tr>
        <td>
          {cliente.first_name} {cliente.last_name}
        </td>
        <td>{cliente.email}</td>
        <td>{cliente.phone || '—'}</td>
        <td>
          <StatusBadge
            label={cliente.is_active ? 'Activa' : 'Inactiva'}
            tone={cliente.is_active ? 'completed' : undefined}
          />
        </td>
        <td>
          <button type="button" className="btn btn-plain" onClick={onToggle}>
            <Icon name="mascota" size={14} />
            <span>{expandido ? 'Ocultar' : 'Ver mascotas'}</span>
          </button>
        </td>
        {puedeActivar ? (
          <td>
            <button
              type="button"
              className={cliente.is_active ? 'btn btn-plain' : 'btn btn-green'}
              disabled={cambiandoEstado}
              onClick={onCambiarEstado}
            >
              {cliente.is_active ? 'Desactivar' : 'Activar'}
            </button>
          </td>
        ) : null}
      </tr>
      {expandido ? (
        <tr>
          <td colSpan={puedeActivar ? 6 : 5}>
            <ClientPets ownerId={cliente.id} />
          </td>
        </tr>
      ) : null}
    </Fragment>
  )
}
