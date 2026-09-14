// Códigos de país para los teléfonos.
//
// Perú va primero porque es donde está la clínica; el resto son los países de
// donde más llega gente a Trujillo, en orden alfabético. El ejemplo de cada uno
// es el formato de un celular de ese país y sirve de placeholder.

export const PAISES = [
  { iso: 'PE', nombre: 'Perú', prefijo: '+51', ejemplo: '987 654 321' },
  { iso: 'AR', nombre: 'Argentina', prefijo: '+54', ejemplo: '11 2345 6789' },
  { iso: 'BO', nombre: 'Bolivia', prefijo: '+591', ejemplo: '712 34567' },
  { iso: 'BR', nombre: 'Brasil', prefijo: '+55', ejemplo: '11 91234 5678' },
  { iso: 'CL', nombre: 'Chile', prefijo: '+56', ejemplo: '9 1234 5678' },
  { iso: 'CO', nombre: 'Colombia', prefijo: '+57', ejemplo: '321 123 4567' },
  { iso: 'EC', nombre: 'Ecuador', prefijo: '+593', ejemplo: '99 123 4567' },
  { iso: 'ES', nombre: 'España', prefijo: '+34', ejemplo: '612 34 56 78' },
  { iso: 'US', nombre: 'Estados Unidos', prefijo: '+1', ejemplo: '201 555 0123' },
  { iso: 'MX', nombre: 'México', prefijo: '+52', ejemplo: '55 1234 5678' },
  { iso: 'PY', nombre: 'Paraguay', prefijo: '+595', ejemplo: '981 123 456' },
  { iso: 'UY', nombre: 'Uruguay', prefijo: '+598', ejemplo: '94 123 456' },
  { iso: 'VE', nombre: 'Venezuela', prefijo: '+58', ejemplo: '412 123 4567' },
] as const

export type PaisTelefonico = (typeof PAISES)[number]
export type CodigoDePais = PaisTelefonico['iso']

const PAIS_POR_DEFECTO = PAISES[0]

// Del prefijo más largo al más corto: "+591" tiene que ganarle a un "+5" si
// alguna vez se agrega uno.
const POR_LARGO_DE_PREFIJO = [...PAISES].sort((a, b) => b.prefijo.length - a.prefijo.length)

export function paisPorIso(iso: string): PaisTelefonico {
  return PAISES.find((pais) => pais.iso === iso) ?? PAIS_POR_DEFECTO
}

/**
 * Separa un teléfono guardado en país y número.
 *
 * Un número sin código, como los cargados antes de existir el selector, se
 * toma como peruano.
 */
export function separarTelefono(valor: string): { iso: CodigoDePais; numero: string } {
  const limpio = valor.trimStart()
  const pais = POR_LARGO_DE_PREFIJO.find((candidato) => limpio.startsWith(candidato.prefijo))
  if (pais === undefined) {
    return { iso: PAIS_POR_DEFECTO.iso, numero: limpio }
  }
  return { iso: pais.iso, numero: limpio.slice(pais.prefijo.length).replace(/^\s/u, '') }
}

/** El teléfono tal como se guarda: "+51 987 654 321", o vacío si no hay número. */
export function unirTelefono(iso: string, numero: string): string {
  return numero.trim() === '' ? '' : `${paisPorIso(iso).prefijo} ${numero}`
}

/** Deja dígitos y espacios mientras la persona escribe el número. */
export function soloNumeroNacional(valor: string): string {
  return valor.replace(/[^\d ]/gu, '').replace(/^ +/u, '')
}
