// Fechas en la zona horaria de la clinica.
//
// El servidor agrupa horas libres y turnos por el dia calendario de la clinica,
// no por el de quien mira la pantalla. Si alguien entra desde otra zona horaria,
// "lunes 14" tiene que seguir siendo el lunes 14 en Trujillo. Lima no tiene
// horario de verano, asi que el desplazamiento es fijo, igual que en el servidor.

export const CLINIC_TIME_ZONE = 'America/Lima'
export const DIAS_A_MOSTRAR = 14
export const DIAS_DE_LA_SEMANA = 7

const CLINIC_UTC_OFFSET = '-05:00'
const MS_POR_DIA = 86_400_000

// `en-CA` escribe la fecha como AAAA-MM-DD, que es la forma de la API.
const CLAVE = new Intl.DateTimeFormat('en-CA', {
  timeZone: CLINIC_TIME_ZONE,
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
})
// Una clave de dia se lee a mediodia UTC y se formatea en UTC: asi ningun
// desplazamiento horario la corre al dia anterior.
const SEMANA = new Intl.DateTimeFormat('es-PE', { timeZone: 'UTC', weekday: 'short' })
const MES = new Intl.DateTimeFormat('es-PE', { timeZone: 'UTC', month: 'short' })
const DIA_LARGO = new Intl.DateTimeFormat('es-PE', {
  timeZone: 'UTC',
  weekday: 'long',
  day: 'numeric',
  month: 'long',
})
const DIA_Y_MES = new Intl.DateTimeFormat('es-PE', {
  timeZone: 'UTC',
  day: 'numeric',
  month: 'long',
})
const HORA = new Intl.DateTimeFormat('es-PE', {
  timeZone: CLINIC_TIME_ZONE,
  hour: 'numeric',
  minute: '2-digit',
})
// Los turnos se leen mejor en 24 horas: "20:00 a 08:00" no deja dudas.
const HORA_24 = new Intl.DateTimeFormat('es-PE', {
  timeZone: CLINIC_TIME_ZONE,
  hour: '2-digit',
  minute: '2-digit',
  hourCycle: 'h23',
})
const DIA_DE_INSTANTE = new Intl.DateTimeFormat('es-PE', {
  timeZone: CLINIC_TIME_ZONE,
  weekday: 'long',
  day: 'numeric',
  month: 'long',
})

function mediodia(clave: string): Date {
  return new Date(`${clave}T12:00:00Z`)
}

/** La clave AAAA-MM-DD de hoy en la fecha de la clinica. */
export function hoyEnClinica(ahora: Date = new Date()): string {
  return CLAVE.format(ahora)
}

export function sumarDias(clave: string, dias: number): string {
  return new Date(mediodia(clave).getTime() + dias * MS_POR_DIA).toISOString().slice(0, 10)
}

/** Las claves AAAA-MM-DD de hoy y los dias siguientes, en la fecha de la clinica. */
export function diasDesdeHoy(cantidad: number, ahora: Date = new Date()): string[] {
  const hoy = hoyEnClinica(ahora)
  return Array.from({ length: cantidad }, (_, indice) => sumarDias(hoy, indice))
}

/** 0 es lunes y 6 domingo, igual que en el servidor. */
export function diaDeLaSemana(clave: string): number {
  return (mediodia(clave).getUTCDay() + DIAS_DE_LA_SEMANA - 1) % DIAS_DE_LA_SEMANA
}

export function lunesDe(clave: string): string {
  return sumarDias(clave, -diaDeLaSemana(clave))
}

export function diasDeLaSemana(lunes: string): string[] {
  return Array.from({ length: DIAS_DE_LA_SEMANA }, (_, indice) => sumarDias(lunes, indice))
}

/** El instante, en ISO y UTC, de una fecha y una hora HH:MM de la clinica. */
export function instanteEnClinica(clave: string, hora = '00:00'): string {
  return new Date(`${clave}T${hora}:00${CLINIC_UTC_OFFSET}`).toISOString()
}

/** Desde la medianoche del lunes hasta la del lunes siguiente, en la clinica. */
export function ventanaDeSemana(lunes: string): { desde: string; hasta: string } {
  return {
    desde: instanteEnClinica(lunes),
    hasta: instanteEnClinica(sumarDias(lunes, DIAS_DE_LA_SEMANA)),
  }
}

/** El dia de la clinica en el que cae un instante. */
export function claveDeInstante(instante: string): string {
  return CLAVE.format(new Date(instante))
}

export function partesDelDia(clave: string): { semana: string; numero: number; mes: string } {
  const fecha = mediodia(clave)
  return { semana: SEMANA.format(fecha), numero: fecha.getUTCDate(), mes: MES.format(fecha) }
}

export function formatearDia(clave: string): string {
  return DIA_LARGO.format(mediodia(clave))
}

export function formatearRangoDeDias(desde: string, hasta: string): string {
  return DIA_Y_MES.formatRange(mediodia(desde), mediodia(hasta))
}

export function formatearHora(instante: string): string {
  return HORA.format(new Date(instante))
}

export function formatearHora24(instante: string): string {
  return HORA_24.format(new Date(instante))
}

export function formatearDiaDeInstante(instante: string): string {
  return DIA_DE_INSTANTE.format(new Date(instante))
}
