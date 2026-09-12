type Extra = 'none' | 'review' | 'complaint' | 'hospitalization'

interface AppointmentExtraButtonsProps {
  readonly extra: Extra
  readonly esStaff: boolean
  readonly puedeResenar: boolean
  readonly puedeInternar: boolean
  readonly onAlternar: (valor: Extra) => void
}

/** Botones que abren o cierran el panel extra de una cita: reseña, reclamo o internación. */
export default function AppointmentExtraButtons({
  extra,
  esStaff,
  puedeResenar,
  puedeInternar,
  onAlternar,
}: AppointmentExtraButtonsProps) {
  return (
    <>
      {puedeResenar ? (
        <button
          type="button"
          className="btn btn-plain"
          onClick={() => {
            onAlternar('review')
          }}
        >
          {extra === 'review' ? 'Ocultar reseña' : 'Dejar reseña'}
        </button>
      ) : null}
      {!esStaff ? (
        <button
          type="button"
          className="btn btn-plain"
          onClick={() => {
            onAlternar('complaint')
          }}
        >
          {extra === 'complaint' ? 'Ocultar reclamo' : 'Presentar reclamo'}
        </button>
      ) : null}
      {puedeInternar ? (
        <button
          type="button"
          className="btn btn-plain"
          onClick={() => {
            onAlternar('hospitalization')
          }}
        >
          {extra === 'hospitalization' ? 'Ocultar internación' : 'Internar'}
        </button>
      ) : null}
    </>
  )
}
