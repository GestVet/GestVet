import ConfirmDialog from '../../components/ConfirmDialog'
import Icon from '../../components/Icon'
import type { IconName } from '../../components/icons'
import { Button } from '../../components/ui/button'
import { horaDeHabilitacion } from './appointmentSummary'

interface CloseAppointmentButtonProps {
  readonly label: string
  readonly icon: IconName
  readonly variant: 'success' | 'outline'
  /** Desde cuándo lo acepta el servidor; antes, el botón explica por qué no. */
  readonly availableFrom: string
  readonly now: number
  readonly busy: boolean
  readonly dialogTitle: string
  readonly dialogDescription: string
  readonly onConfirm: () => void
}

/**
 * Completar o marcar la inasistencia: un clic no alcanza, pide confirmación.
 *
 * Antes de su hora el botón queda deshabilitado con la hora en que se
 * habilita. El servidor aplica la misma regla y es el que decide.
 */
export default function CloseAppointmentButton({
  label,
  icon,
  variant,
  availableFrom,
  now,
  busy,
  dialogTitle,
  dialogDescription,
  onConfirm,
}: CloseAppointmentButtonProps) {
  const contenido = (
    <>
      <Icon name={icon} size={14} />
      <span>{label}</span>
    </>
  )

  if (now < Date.parse(availableFrom)) {
    return (
      <span className="flex flex-col items-start gap-0.5">
        <Button type="button" size="sm" variant={variant} disabled>
          {contenido}
        </Button>
        <span className="text-xs text-muted-foreground">
          Desde el {horaDeHabilitacion(availableFrom)}
        </span>
      </span>
    )
  }

  return (
    <ConfirmDialog
      trigger={
        <Button type="button" size="sm" variant={variant} disabled={busy}>
          {contenido}
        </Button>
      }
      title={dialogTitle}
      description={dialogDescription}
      confirmLabel={label}
      confirmVariant="default"
      onConfirm={onConfirm}
    />
  )
}
