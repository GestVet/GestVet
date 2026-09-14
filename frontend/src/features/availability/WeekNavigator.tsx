import Icon from '../../components/Icon'
import { Button } from '../../components/ui/button'
import {
  formatearRangoDeDias,
  hoyEnClinica,
  lunesDe,
  sumarDias,
} from '../../services/clinicTime'

interface WeekNavigatorProps {
  /** AAAA-MM-DD del lunes de la semana que se ve. */
  readonly lunes: string
  readonly onChange: (lunes: string) => void
}

export default function WeekNavigator({ lunes, onChange }: WeekNavigatorProps) {
  const estaSemana = lunesDe(hoyEnClinica())

  return (
    <div className="flex flex-wrap items-center gap-2">
      <Button
        type="button"
        variant="outline"
        size="icon"
        aria-label="Semana anterior"
        onClick={() => {
          onChange(sumarDias(lunes, -7))
        }}
      >
        <Icon name="anterior" size={16} />
      </Button>
      <p className="m-0 min-w-44 text-center text-sm font-medium" aria-live="polite">
        {formatearRangoDeDias(lunes, sumarDias(lunes, 6))}
      </p>
      <Button
        type="button"
        variant="outline"
        size="icon"
        aria-label="Semana siguiente"
        onClick={() => {
          onChange(sumarDias(lunes, 7))
        }}
      >
        <Icon name="siguiente" size={16} />
      </Button>
      <Button
        type="button"
        variant="ghost"
        size="sm"
        disabled={lunes === estaSemana}
        onClick={() => {
          onChange(estaSemana)
        }}
      >
        Esta semana
      </Button>
    </div>
  )
}
