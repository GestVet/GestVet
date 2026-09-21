import StatusBadge from '../../components/StatusBadge'

interface AppointmentTypeCellProps {
  readonly name: string
  readonly isEmergency: boolean
}

/** El motivo de la cita, con la marca de emergencia cuando lo es. */
export default function AppointmentTypeCell({ name, isEmergency }: AppointmentTypeCellProps) {
  return (
    <div className="flex min-w-28 flex-col items-start gap-1">
      <span>{name || '—'}</span>
      {isEmergency ? <StatusBadge label="Emergencia" tone="cancelled" /> : null}
    </div>
  )
}
