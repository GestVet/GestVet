// Las fechas del carnet son días, no instantes: se muestran sin correrlas de zona.
const FECHA = new Intl.DateTimeFormat('es-PE', { dateStyle: 'medium', timeZone: 'UTC' })

export function formatearFechaDeVacuna(dia: string): string {
  return FECHA.format(new Date(`${dia}T00:00:00Z`))
}
