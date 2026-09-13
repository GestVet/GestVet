const FILAS = ['Citas', 'Mascotas', 'Historias clínicas', 'Indicadores'] as const

/**
 * Miniatura del sistema sobre la foto. Los nombres son reales; no hay cifras.
 */
export default function HomeProductPreview() {
  return (
    <div
      aria-hidden="true"
      className="w-44 rounded-xl bg-card p-3 shadow-[0_10px_28px_rgb(0_75_141_/_0.18)] sm:w-52"
    >
      <p className="m-0 mb-3 font-heading text-sm font-bold text-primary">GestVet</p>
      <ul className="m-0 flex list-none flex-col gap-2 p-0">
        {FILAS.map((fila) => (
          <li
            key={fila}
            className="rounded-lg bg-muted px-2.5 py-2 text-xs font-medium text-foreground"
          >
            {fila}
          </li>
        ))}
      </ul>
    </div>
  )
}
