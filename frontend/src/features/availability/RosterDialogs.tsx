import type { UserResponse } from '../../api/types'
import FormDialog from '../../components/FormDialog'
import ShiftForm, { type TurnoInicial } from './ShiftForm'
import WeeklyPlanForm from './WeeklyPlanForm'

/** Qué ventana está abierta en la pantalla de turnos. */
export type DialogoDeTurnos =
  | ({ readonly tipo: 'turno' } & TurnoInicial)
  | { readonly tipo: 'semanal' }
  | null

interface RosterDialogsProps {
  readonly dialogo: DialogoDeTurnos
  readonly veterinarios: readonly UserResponse[]
  readonly onClose: () => void
}

/** Las dos formas de cargar turnos: uno puntual o un horario que se repite. */
export default function RosterDialogs({ dialogo, veterinarios, onClose }: RosterDialogsProps) {
  const alCambiar = (abierto: boolean) => {
    if (!abierto) {
      onClose()
    }
  }

  return (
    <>
      <FormDialog
        open={dialogo?.tipo === 'turno'}
        onOpenChange={alCambiar}
        title="Asignar un turno"
        description="Para un día puntual o un reemplazo. Elige un horario rápido o ajusta las horas."
        size="lg"
      >
        {dialogo?.tipo === 'turno' ? (
          <ShiftForm veterinarios={veterinarios} inicial={dialogo} onDone={onClose} />
        ) : null}
      </FormDialog>
      <FormDialog
        open={dialogo?.tipo === 'semanal'}
        onOpenChange={alCambiar}
        title="Horario semanal"
        description="Repite el mismo horario varias semanas. Si algún día choca con otro turno, no se asigna ninguno."
        size="lg"
      >
        {dialogo?.tipo === 'semanal' ? (
          <WeeklyPlanForm veterinarios={veterinarios} onDone={onClose} />
        ) : null}
      </FormDialog>
    </>
  )
}
