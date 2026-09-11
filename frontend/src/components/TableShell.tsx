interface TableShellProps {
  readonly columns: readonly string[]
  readonly isLoading: boolean
  readonly isEmpty: boolean
  readonly emptyMessage: string
  readonly children: React.ReactNode
}

/**
 * Envoltura de tabla con sus dos estados vacios.
 *
 * Cada listado repetia el mismo "cargando", el mismo "no hay nada" y el mismo
 * contenedor con desplazamiento horizontal.
 */
export default function TableShell({
  columns,
  isLoading,
  isEmpty,
  emptyMessage,
  children,
}: TableShellProps) {
  if (isLoading) {
    return <p className="empty">Cargando…</p>
  }
  if (isEmpty) {
    return <p className="empty">{emptyMessage}</p>
  }
  return (
    <div className="table-wrapper">
      <table>
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column}>{column}</th>
            ))}
          </tr>
        </thead>
        <tbody>{children}</tbody>
      </table>
    </div>
  )
}
