export interface BarChartDatum {
  readonly label: string
  readonly value: number
  readonly color: string
}

interface BarChartProps {
  readonly title: string
  readonly data: readonly BarChartDatum[]
  readonly emptyMessage: string
}

/**
 * Gráfico de barras minimalista, sin librería: una sola magnitud por barra,
 * eje de categorías directo abajo, valor directo arriba. Ver
 * frontend/src/index.css para los tokens de color que usa cada barra —
 * siempre los mismos que ya usa el resto de la app, ninguno nuevo.
 */
export default function BarChart({ title, data, emptyMessage }: BarChartProps) {
  const maximo = Math.max(1, ...data.map((item) => item.value))

  return (
    <figure className="m-0 flex flex-col gap-3 rounded-xl bg-card p-4 ring-1 ring-foreground/10">
      <figcaption className="text-sm font-medium text-foreground">{title}</figcaption>
      {data.length === 0 ? (
        <p className="m-0 text-sm text-muted-foreground">{emptyMessage}</p>
      ) : (
        <div className="flex h-40 items-end justify-center gap-4">
          {data.map((item) => (
            <div key={item.label} className="flex h-full w-14 flex-col items-center gap-1.5">
              <span className="text-xs font-medium tabular-nums text-foreground">
                {item.value}
              </span>
              <div className="flex w-full flex-1 items-end justify-center">
                <div
                  title={`${item.label}: ${String(item.value)}`}
                  className="w-6 rounded-t-[4px]"
                  style={{
                    height: `${String((item.value / maximo) * 100)}%`,
                    backgroundColor: item.color,
                    minHeight: item.value > 0 ? '2px' : 0,
                  }}
                />
              </div>
              <span className="text-center text-xs text-muted-foreground">{item.label}</span>
            </div>
          ))}
        </div>
      )}
    </figure>
  )
}
