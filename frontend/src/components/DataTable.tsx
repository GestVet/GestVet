import {
  type ColumnDef,
  createExpandedRowModel,
  flexRender,
  type Row,
  type RowData,
  rowExpandingFeature,
  tableFeatures,
  useTable,
} from '@tanstack/react-table'
import { Fragment, type ReactNode, useMemo } from 'react'

import { usePagination } from '../hooks/usePagination'
import EmptyState from './EmptyState'
import TablePagination from './TablePagination'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table'

/** Lo que una celda sabe de su fila, ademas del dato. */
export interface DataRowContext {
  readonly isExpanded: boolean
  readonly toggleExpanded: () => void
}

/**
 * Una columna, descrita sin tipos de TanStack.
 *
 * Cada listado declara sus columnas con esta forma y la tabla las traduce. Asi
 * las pantallas no dependen de los genericos de la version de TanStack Table,
 * que cambiaron entera de la 8 a la 9.
 */
export interface DataColumn<TData extends RowData> {
  readonly id: string
  readonly header: string
  readonly cell: (row: TData, context: DataRowContext) => ReactNode
  /** Clases de la celda, por ejemplo para que un texto largo pueda partirse. */
  readonly className?: string
}

const features = tableFeatures({
  rowExpandingFeature,
  expandedRowModel: createExpandedRowModel(),
})

function rowContext<TData extends RowData>(row: Row<typeof features, TData>): DataRowContext {
  return {
    isExpanded: row.getIsExpanded(),
    toggleExpanded: () => {
      row.toggleExpanded()
    },
  }
}

function toColumnDef<TData extends RowData>(
  column: DataColumn<TData>,
): ColumnDef<typeof features, TData> {
  return {
    id: column.id,
    header: column.header,
    cell: ({ row }) => column.cell(row.original, rowContext(row)),
  }
}

interface DataTableProps<TData extends RowData> {
  readonly columns: readonly DataColumn<TData>[]
  readonly data: readonly TData[]
  readonly isLoading: boolean
  readonly emptyMessage: string
  readonly getRowId: (row: TData, index: number) => string
  /** Contenido que se despliega debajo de una fila. Sin el, ninguna se abre. */
  readonly renderExpanded?: (row: TData) => ReactNode
  /** Filas por página. Sin él, la tabla muestra todas las filas juntas. */
  readonly pageSize?: number
}

/**
 * Tabla de datos de toda la aplicacion, con TanStack Table y la tabla de shadcn.
 *
 * Resuelve lo comun a cada listado: el estado de carga, el vacio, el
 * desplazamiento horizontal en pantallas angostas y las filas que se
 * despliegan. En el celular la tabla se desplaza en vez de apilarse: WCAG
 * exime a las tablas de datos del reflujo, y apilarla le quita las cabeceras
 * al lector de pantalla.
 */
export default function DataTable<TData extends RowData>({
  columns,
  data,
  isLoading,
  emptyMessage,
  getRowId,
  renderExpanded,
  pageSize,
}: DataTableProps<TData>) {
  const pagina = usePagination(data, pageSize)
  const rows = useMemo(() => [...pagina.visibles], [pagina.visibles])
  const columnDefs = useMemo(() => columns.map(toColumnDef), [columns])
  const cellClasses = useMemo(
    () => new Map(columns.map((column) => [column.id, column.className ?? ''])),
    [columns],
  )

  const table = useTable({
    features,
    columns: columnDefs,
    data: rows,
    getRowId,
    getRowCanExpand: () => renderExpanded !== undefined,
  })

  if (isLoading) {
    return <EmptyState title="Cargando…" />
  }
  if (data.length === 0) {
    return <EmptyState title={emptyMessage} />
  }

  return (
    <div className="flex flex-col gap-3">
    <div className="rounded-xl bg-card ring-1 ring-foreground/10">
      <Table>
        <TableHeader>
          {table.getHeaderGroups().map((headerGroup) => (
            <TableRow key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <TableHead key={header.id} className="px-3">
                  {flexRender(header.column.columnDef.header, header.getContext())}
                </TableHead>
              ))}
            </TableRow>
          ))}
        </TableHeader>
        <TableBody>
          {table.getRowModel().rows.map((row) => (
            <Fragment key={row.id}>
              <TableRow data-state={row.getIsExpanded() ? 'open' : undefined}>
                {row.getAllCells().map((cell) => (
                  <TableCell
                    key={cell.id}
                    className={`px-3 py-2.5 ${cellClasses.get(cell.column.id) ?? ''}`}
                  >
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </TableCell>
                ))}
              </TableRow>
              {row.getIsExpanded() && renderExpanded !== undefined ? (
                <TableRow className="hover:bg-transparent">
                  <TableCell
                    colSpan={row.getAllCells().length}
                    className="bg-muted/40 p-4 whitespace-normal"
                  >
                    {renderExpanded(row.original)}
                  </TableCell>
                </TableRow>
              ) : null}
            </Fragment>
          ))}
        </TableBody>
      </Table>
    </div>
    {pagina.total > 1 ? (
      <TablePagination actual={pagina.actual} total={pagina.total} onChange={pagina.irA} />
    ) : null}
    </div>
  )
}
