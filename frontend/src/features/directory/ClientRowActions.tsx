import Icon from '../../components/Icon'

interface ClientRowActionsProps {
  readonly expandido: boolean
  readonly onToggle: () => void
  readonly contactoPendiente: boolean
  readonly completandoContacto: boolean
  readonly onToggleContacto: () => void
}

export default function ClientRowActions({
  expandido,
  onToggle,
  contactoPendiente,
  completandoContacto,
  onToggleContacto,
}: ClientRowActionsProps) {
  return (
    <div className="row-actions">
      <button type="button" className="btn btn-plain" onClick={onToggle}>
        <Icon name="mascota" size={14} />
        <span>{expandido ? 'Ocultar' : 'Ver mascotas'}</span>
      </button>
      {contactoPendiente ? (
        <button type="button" className="btn btn-plain" onClick={onToggleContacto}>
          {completandoContacto ? 'Ocultar' : 'Completar contacto'}
        </button>
      ) : null}
    </div>
  )
}
