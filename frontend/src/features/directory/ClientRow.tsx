import { Fragment, useState } from 'react'

import type { UserResponse } from '../../api/types'
import StatusBadge from '../../components/StatusBadge'
import ClientPets from './ClientPets'
import ClientRowActions from './ClientRowActions'
import ClientStatusToggle from './ClientStatusToggle'
import CompleteContactForm from './CompleteContactForm'

// El dominio de relleno que usa el alta exprés de emergencia: mientras el
// correo de un cliente termine así, esa cuenta no puede entrar por su cuenta.
const PLACEHOLDER_EMAIL_SUFFIX = '@pendiente.gestvet.local'

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
  const [completandoContacto, setCompletandoContacto] = useState(false)
  const contactoPendiente = cliente.email.endsWith(PLACEHOLDER_EMAIL_SUFFIX)
  const columnas = puedeActivar ? 6 : 5

  return (
    <Fragment>
      <tr>
        <td>
          {cliente.first_name} {cliente.last_name}
        </td>
        <td>
          {contactoPendiente ? (
            <StatusBadge label="Correo pendiente" tone="pending" />
          ) : (
            cliente.email
          )}
        </td>
        <td>{cliente.phone || '—'}</td>
        <td>
          <StatusBadge
            label={cliente.is_active ? 'Activa' : 'Inactiva'}
            tone={cliente.is_active ? 'completed' : undefined}
          />
        </td>
        <td>
          <ClientRowActions
            expandido={expandido}
            onToggle={onToggle}
            contactoPendiente={contactoPendiente}
            completandoContacto={completandoContacto}
            onToggleContacto={() => {
              setCompletandoContacto(!completandoContacto)
            }}
          />
        </td>
        {puedeActivar ? (
          <td>
            <ClientStatusToggle
              isActive={cliente.is_active}
              disabled={cambiandoEstado}
              onToggle={onCambiarEstado}
            />
          </td>
        ) : null}
      </tr>
      {completandoContacto ? (
        <tr>
          <td colSpan={columnas}>
            <CompleteContactForm clientId={cliente.id} phone={cliente.phone} />
          </td>
        </tr>
      ) : null}
      {expandido ? (
        <tr>
          <td colSpan={columnas}>
            <ClientPets ownerId={cliente.id} />
          </td>
        </tr>
      ) : null}
    </Fragment>
  )
}
