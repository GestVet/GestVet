// Códigos de país para los teléfonos.
//
// Salen de `libphonenumber-js`, la versión en JavaScript de la librería de
// Google para teléfonos: trae el código de cada país y un celular de ejemplo,
// que sirve de placeholder. Los nombres los da el navegador en español, así no
// hay una lista de 245 países que mantener a mano.

import {
  type CountryCode,
  getCountries,
  getCountryCallingCode,
  getExampleNumber,
  type PhoneNumber,
  parsePhoneNumberFromString,
} from 'libphonenumber-js'
import metadata from 'libphonenumber-js/min/metadata'
import ejemplos from 'libphonenumber-js/mobile/examples'

export type CodigoDePais = CountryCode

export interface PaisTelefonico {
  readonly iso: CodigoDePais
  readonly nombre: string
  readonly prefijo: string
  readonly ejemplo: string
}

const NOMBRES = new Intl.DisplayNames(['es'], { type: 'region' })

// Perú primero porque es donde está la clínica; después, los países de donde
// más llega gente a Trujillo.
const ISO_FRECUENTES: readonly CodigoDePais[] = [
  'PE',
  'VE',
  'CO',
  'EC',
  'BO',
  'CL',
  'AR',
  'BR',
  'MX',
  'US',
  'ES',
]

function crearPais(iso: CodigoDePais): PaisTelefonico {
  const prefijo = `+${getCountryCallingCode(iso)}`
  const internacional = getExampleNumber(iso, ejemplos)?.formatInternational() ?? ''
  return {
    iso,
    nombre: NOMBRES.of(iso) ?? iso,
    prefijo,
    // Sin el código, que ya muestra el selector, y sin guiones, que el campo
    // no deja escribir.
    ejemplo: internacional.slice(prefijo.length).replaceAll('-', ' ').trim(),
  }
}

/** Todos los países, por nombre. */
export const PAISES: readonly PaisTelefonico[] = getCountries()
  .map(crearPais)
  .sort((a, b) => a.nombre.localeCompare(b.nombre, 'es'))

const POR_ISO = new Map<string, PaisTelefonico>(PAISES.map((pais) => [pais.iso, pais]))
const PAIS_POR_DEFECTO = crearPais('PE')

export function paisPorIso(iso: string): PaisTelefonico {
  return POR_ISO.get(iso) ?? PAIS_POR_DEFECTO
}

export const PAISES_FRECUENTES: readonly PaisTelefonico[] = ISO_FRECUENTES.map(paisPorIso)

// Varios países comparten código: el +1 es de Estados Unidos, Canadá y buena
// parte del Caribe. La metadata pone primero al principal de cada código.
function principalDelCodigo(codigo: string): CodigoDePais | undefined {
  // El tipo no lo dice, pero un código que no existe no está en la tabla.
  if (!(codigo in metadata.country_calling_codes)) {
    return undefined
  }
  return metadata.country_calling_codes[codigo][0]
}

// Un número a medio escribir todavía no se deja leer entero, pero su código
// ya está: es lo que va entre el "+" y el primer espacio.
function codigoDelTelefono(telefono: string, leido: PhoneNumber | undefined): string | undefined {
  return leido?.countryCallingCode ?? /^\+(\d{1,3})\s/u.exec(telefono)?.[1]
}

function paisDelTelefono(
  telefono: string,
  preferido: CodigoDePais | undefined,
): PaisTelefonico | undefined {
  const leido = parsePhoneNumberFromString(telefono)
  const codigo = codigoDelTelefono(telefono, leido)
  if (codigo === undefined) {
    return undefined
  }
  if (preferido !== undefined && getCountryCallingCode(preferido) === codigo) {
    return paisPorIso(preferido)
  }
  const iso = leido?.country ?? principalDelCodigo(codigo)
  return iso === undefined ? undefined : paisPorIso(iso)
}

/**
 * Separa un teléfono guardado en país y número.
 *
 * `preferido` es el país elegido en el selector: mientras se escribe un +1 no
 * hay forma de saber si es de Canadá o de Estados Unidos, y manda la elección.
 * Un número sin código, como los cargados antes de existir el selector, se
 * toma como peruano.
 */
export function separarTelefono(
  valor: string,
  preferido?: CodigoDePais,
): { iso: CodigoDePais; numero: string } {
  const limpio = valor.trimStart()
  const pais = limpio.startsWith('+') ? paisDelTelefono(limpio, preferido) : undefined
  if (pais === undefined) {
    return { iso: PAIS_POR_DEFECTO.iso, numero: limpio }
  }
  return { iso: pais.iso, numero: limpio.slice(pais.prefijo.length).trimStart() }
}

/** El teléfono tal como se guarda: "+51 987 654 321", o vacío si no hay número. */
export function unirTelefono(iso: string, numero: string): string {
  return numero.trim() === '' ? '' : `${paisPorIso(iso).prefijo} ${numero}`
}

/** Deja dígitos y espacios mientras la persona escribe el número. */
export function soloNumeroNacional(valor: string): string {
  return valor.replace(/[^\d ]/gu, '').replace(/^ +/u, '')
}

/** Para buscar sin que importen tildes ni mayúsculas: "peru" encuentra Perú. */
export function sinTildes(texto: string): string {
  return texto.normalize('NFD').replace(/\p{Diacritic}/gu, '').toLowerCase()
}
