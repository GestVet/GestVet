import { z } from 'zod'

// Reglas de formulario que comparten pantallas de distintas partes: textos
// libres, montos y los datos de una mascota.
//
// Los limites repiten los del backend. Repetirlos no duplica la regla, que
// sigue viviendo en el servidor: avisa mientras la persona escribe.

/** Un texto que explica algo necesita al menos unas palabras. */
export const MIN_TEXTO = 5

const HOY = () => new Date().toISOString().slice(0, 10)
const MAX_AÑOS_DE_VIDA = 60

function maximo(max: number): string {
  return `Usa como máximo ${String(max)} caracteres`
}

/** Un texto obligatorio: se recorta y necesita al menos cinco caracteres. */
export function textoObligatorio(max: number, pedido: string) {
  return z.string().trim().min(1, pedido).min(MIN_TEXTO, `${pedido} (al menos ${String(MIN_TEXTO)} caracteres)`).max(max, maximo(max))
}

export function textoOpcional(max: number) {
  return z.string().trim().max(max, maximo(max))
}

interface NumeroDecimal {
  readonly max: number
  readonly decimales: number
  readonly unidad: string
  readonly obligatorio?: boolean
}

/**
 * Un numero positivo escrito en un campo de texto, con tope y decimales.
 *
 * Vacio vale cuando el campo es opcional. El tope no es arbitrario: un peso de
 * 1800 kg no es un gran danes, es un error de tipeo.
 */
export function decimalRule({ max, decimales, unidad, obligatorio = false }: NumeroDecimal) {
  const formato = new RegExp(`^\\d+(?:[.,]\\d{1,${String(decimales)}})?$`, 'u')
  return z
    .string()
    .trim()
    .refine((valor) => !obligatorio || valor !== '', 'Escribe un valor')
    .refine(
      (valor) => valor === '' || formato.test(valor),
      `Escribe un número con hasta ${String(decimales)} decimales`,
    )
    .refine(
      (valor) => valor === '' || Number(valor.replace(',', '.')) > 0,
      'Tiene que ser mayor que cero',
    )
    .refine(
      (valor) => valor === '' || Number(valor.replace(',', '.')) <= max,
      `Como máximo ${String(max)} ${unidad}. Revisa el dato`,
    )
}

/** El valor que espera la API: con punto decimal, o `null` si esta vacio. */
export function decimalParaApi(valor: string): string | null {
  const limpio = valor.trim().replace(',', '.')
  return limpio === '' ? null : limpio
}

// Letras, numeros, espacios y los signos de un nombre: "Rocky", "Luna 2", "D'Artagnan".
const NOMBRE_DE_MASCOTA = /^[\p{L}\d](?:[\p{L}\d '.-]*[\p{L}\d.])?$/u

export const MAX_NOMBRE_DE_MASCOTA = 60

export const nombreDeMascotaRule = z
  .string()
  .trim()
  .min(1, 'Escribe el nombre')
  .max(MAX_NOMBRE_DE_MASCOTA, maximo(MAX_NOMBRE_DE_MASCOTA))
  .regex(NOMBRE_DE_MASCOTA, 'Usa letras, números, espacios, guiones o apóstrofos')

export function limitesDeNacimiento(): { min: string; max: string } {
  const hoy = HOY()
  const min = `${String(Number(hoy.slice(0, 4)) - MAX_AÑOS_DE_VIDA)}${hoy.slice(4)}`
  return { min, max: hoy }
}

export const fechaDeNacimientoRule = z
  .string()
  .regex(/^\d{4}-\d{2}-\d{2}$/u, 'Indica la fecha de nacimiento')
  .refine((valor) => valor <= limitesDeNacimiento().max, 'La fecha no puede estar en el futuro')
  .refine(
    (valor) => valor >= limitesDeNacimiento().min,
    `Ninguna mascota vive más de ${String(MAX_AÑOS_DE_VIDA)} años. Revisa el año`,
  )

// Un microchip ISO tiene 15 digitos; los mas antiguos, 9 o 10.
export const microchipRule = z
  .string()
  .trim()
  .regex(/^(?:\d{9,15})?$/u, 'El microchip tiene de 9 a 15 dígitos, sin espacios ni letras')

/** Deja solo los digitos mientras la persona escribe. */
export function soloDigitosDeMicrochip(valor: string): string {
  return valor.replace(/\D/gu, '').slice(0, 15)
}
