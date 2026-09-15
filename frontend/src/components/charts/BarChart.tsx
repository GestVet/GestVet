import type { ReactNode } from 'react'

export interface BarChartDatum {
  readonly label: string
  readonly value: number
  readonly color: string
}

interface BarChartProps {
  readonly title: string
  readonly data: readonly BarChartDatum[]
  readonly emptyMessage: string
  /** Barras acostadas, para muchas categorías o nombres largos que no entran abajo. */
  readonly horizontal?: boolean
}

/**
 * Gráfico de barras minimalista, sin librería: una sola magnitud por barra,
 * categoría y valor escritos directo junto a cada barra. Ver
 * frontend/src/index.css para los tokens de color que usa cada barra —
 * siempre los mismos que ya usa el resto de la app, ninguno nuevo.
 */
export default function BarChart({ title, data, emptyMessage, horizontal = false }: BarChartProps) {
  const maximo = Math.max(1, ...data.map((item) => item.value))
  const porcentaje = (valor: number) => `${String((valor / maximo) * 100)}%`
  const tooltip = (item: BarChartDatum) => `${item.label}: ${String(item.value)}`
  const alMenosUnPixel = (valor: number) => (valor > 0 ? '2px' : 0)

  let contenido: ReactNode
  if (data.length === 0) {
    contenido = <p className="m-0 text-sm text-muted-foreground">{emptyMessage}</p>
  } else if (horizontal) {
    contenido = (
      <div className="flex flex-col gap-2">
        {data.map((item) => (
          <div key={item.label} className="grid grid-cols-[minmax(0,11rem)_1fr] items-center gap-3">
            <span className="text-xs text-muted-foreground">{item.label}</span>
            <div className="flex items-center gap-2">
              <div
                title={tooltip(item)}
                className="h-5 rounded-r-[4px]"
                style={{
                  width: porcentaje(item.value),
                  backgroundColor: item.color,
                  minWidth: alMenosUnPixel(item.value),
                }}
              />
              <span className="text-xs font-medium tabular-nums text-foreground">{item.value}</span>
            </div>
          </div>
        ))}
      </div>
    )
  } else {
    contenido = (
      <div className="flex h-40 items-end justify-center gap-4">
        {data.map((item) => (
          <div key={item.label} className="flex h-full w-14 flex-col items-center gap-1.5">
            <span className="text-xs font-medium tabular-nums text-foreground">{item.value}</span>
            <div className="flex w-full flex-1 items-end justify-center">
              <div
                title={tooltip(item)}
                className="w-6 rounded-t-[4px]"
                style={{
                  height: porcentaje(item.value),
                  backgroundColor: item.color,
                  minHeight: alMenosUnPixel(item.value),
                }}
              />
            </div>
            <span className="text-center text-xs text-muted-foreground">{item.label}</span>
          </div>
        ))}
      </div>
    )
  }

  return (
    <figure className="m-0 flex flex-col gap-3 rounded-xl bg-card p-4 ring-1 ring-foreground/10">
      <figcaption className="text-sm font-medium text-foreground">{title}</figcaption>
      {contenido}
    </figure>
  )
}
