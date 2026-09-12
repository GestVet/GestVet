import FormMessage from '../../components/FormMessage'
import { Button } from '../../components/ui/button'

interface WalkInEmergencySuccessProps {
  readonly appointmentId: number
  readonly onRestart: () => void
}

export default function WalkInEmergencySuccess({
  appointmentId,
  onRestart,
}: WalkInEmergencySuccessProps) {
  return (
    <div className="flex flex-col items-start gap-4">
      <FormMessage tone="ok">
        Emergencia abierta (#{appointmentId}). Quedó asignada automáticamente a un veterinario
        disponible. El cliente y la mascota ya quedaron registrados — el personal puede completar
        el correo real desde la ficha del cliente cuando haya tiempo.
      </FormMessage>
      <Button type="button" variant="outline" onClick={onRestart}>
        Registrar otra emergencia
      </Button>
    </div>
  )
}
