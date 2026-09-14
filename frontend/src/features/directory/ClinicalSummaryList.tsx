import Icon from '../../components/Icon'
import type { IconName } from '../../components/icons'

interface ClinicalSummaryListProps {
  readonly titulo: string
  readonly icono: IconName
  readonly items: readonly string[]
}

/** Una lista del resumen con IA: las alertas o los pendientes. */
export default function ClinicalSummaryList({ titulo, icono, items }: ClinicalSummaryListProps) {
  return (
    <div className="flex flex-col gap-2">
      <h4 className="m-0 text-sm font-semibold">{titulo}</h4>
      <ul className="m-0 flex list-none flex-col gap-1.5 p-0">
        {items.map((item) => (
          <li key={item} className="flex items-start gap-2 text-sm">
            <span className="mt-0.5 shrink-0 text-muted-foreground">
              <Icon name={icono} size={14} />
            </span>
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}
