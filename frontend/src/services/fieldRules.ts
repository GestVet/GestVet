import { z } from 'zod'

// Reglas de los datos de una persona, compartidas por el registro, el perfil,
// el alta de personal y el alta exprés de emergencias.
//
// Los limites repiten los del backend (RegisterClientRequest y
// UpdateProfileRequest). Repetirlos no duplica la regla, que sigue viviendo en
// el servidor: avisa mientras la persona escribe y no despues de un viaje.

export const MIN_PASSWORD = 10
export const MAX_PASSWORD = 128
export const MAX_NOMBRE = 80
export const MAX_APELLIDO = 120
export const LARGO_DNI = 8
export const MAX_TELEFONO = 20

// Letras de cualquier idioma, con tildes y enie, separadas por un espacio, un
// guion o un apostrofo: "María José", "Pérez-Luna", "O'Brien".
const PALABRAS = /^\p{L}+(?:[ '-]\p{L}+)*$/u
const TELEFONO = /^\+?\d+(?: \d+)*$/u
const MIN_DIGITOS_TELEFONO = 7
const MAX_DIGITOS_TELEFONO = 15

/** Quita lo que no puede ir en un nombre mientras la persona escribe. */
export function soloLetras(valor: string): string {
  return valor.replace(/[^\p{L} '-]/gu, '')
}

/** Deja solo los digitos, para el DNI. */
export function soloDigitos(valor: string): string {
  return valor.replace(/\D/gu, '')
}

/** Deja digitos, espacios y el `+` del codigo de pais. */
export function soloTelefono(valor: string): string {
  return valor.replace(/[^\d +]/gu, '')
}

function contarDigitos(valor: string): number {
  return soloDigitos(valor).length
}

function telefonoValido(valor: string): boolean {
  if (valor === '') {
    return true
  }
  const digitos = contarDigitos(valor)
  return (
    TELEFONO.test(valor) && digitos >= MIN_DIGITOS_TELEFONO && digitos <= MAX_DIGITOS_TELEFONO
  )
}

/** `posesivo` es "tu" cuando la persona escribe lo suyo y "el" cuando carga a otra. */
export function nombreRule(dato: string, max: number, posesivo: 'tu' | 'el' = 'tu'): z.ZodString {
  const sujeto = `${posesivo === 'tu' ? 'Tu' : 'El'} ${dato}`
  return z
    .string()
    .trim()
    .min(1, `Escribe ${posesivo} ${dato}`)
    .max(max, `Usa como máximo ${String(max)} caracteres`)
    .regex(PALABRAS, `${sujeto} solo puede llevar letras, espacios, guiones o apóstrofos`)
}

export const correoRule = z
  .string()
  .trim()
  .toLowerCase()
  .pipe(z.email('Escribe un correo válido, como nombre@correo.com'))

export const dniRule = z
  .string()
  .regex(/^\d{8}$/u, `El DNI tiene ${String(LARGO_DNI)} dígitos, sin puntos ni espacios`)

export const telefonoRule = z
  .string()
  .trim()
  .refine(telefonoValido, 'Escribe un teléfono de 7 a 15 dígitos, como 987 654 321')

export const passwordRule = z
  .string()
  .min(MIN_PASSWORD, `Usa al menos ${String(MIN_PASSWORD)} caracteres`)
  .max(MAX_PASSWORD, `Usa como máximo ${String(MAX_PASSWORD)} caracteres`)
