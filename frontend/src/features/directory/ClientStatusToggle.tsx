interface ClientStatusToggleProps {
  readonly isActive: boolean
  readonly disabled: boolean
  readonly onToggle: () => void
}

export default function ClientStatusToggle({
  isActive,
  disabled,
  onToggle,
}: ClientStatusToggleProps) {
  return (
    <button
      type="button"
      className={isActive ? 'btn btn-plain' : 'btn btn-green'}
      disabled={disabled}
      onClick={onToggle}
    >
      {isActive ? 'Desactivar' : 'Activar'}
    </button>
  )
}
