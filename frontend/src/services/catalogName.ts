// Formato de los nombres del catálogo de especies y razas.
//
// Es la misma regla que aplica el servidor al guardar, repetida acá solo para
// mostrar mientras se escribe cómo va a quedar el nombre. Si las dos llegaran a
// diferir, manda el servidor: lo guardado es lo que devuelve la API.

const MIN_LETRAS = 2
const SIMBOLOS = new Set([' ', "'", '-', '(', ')', '.'])
const CONECTORES = new Set([
  'a',
  'al',
  'con',
  'de',
  'del',
  'e',
  'el',
  'en',
  'la',
  'las',
  'los',
  'o',
  'sin',
  'u',
  'y',
])
const LETRA = /^\p{L}$/u
// Por grafema y no por código: una letra con tilde escrita en dos partes
// ("e" + tilde) cuenta como una sola.
const SEGMENTADOR = new Intl.Segmenter('es', { granularity: 'grapheme' })

function caracteres(texto: string): string[] {
  return Array.from(SEGMENTADOR.segment(texto), (parte) => parte.segment)
}

function esLetra(caracter: string): boolean {
  return LETRA.test(caracter.normalize('NFC'))
}

function letras(palabra: string): string {
  return caracteres(palabra).filter(esLetra).join('')
}

function palabrasDe(texto: string): string[] {
  return texto.split(/\s+/u).filter(Boolean)
}

function empiezaConMayuscula(palabra: string): boolean {
  const soloLetras = letras(palabra)
  const primera = soloLetras.charAt(0)
  const resto = soloLetras.slice(1)
  return primera !== primera.toLowerCase() && resto === resto.toLowerCase()
}

function mayusculaInicial(palabra: string): string {
  const partes = caracteres(palabra)
  const indice = partes.findIndex(esLetra)
  return partes.map((parte, posicion) => (posicion === indice ? parte.toUpperCase() : parte)).join('')
}

/** El motivo por el que un nombre no se puede guardar, o `null` si se puede. */
export function problemaDelNombre(texto: string, maximo: number): string | null {
  const limpio = palabrasDe(texto).join(' ')
  if (letras(limpio).length < MIN_LETRAS) {
    return 'Escribe al menos dos letras'
  }
  if (limpio.length > maximo) {
    return `Usa como máximo ${String(maximo)} caracteres`
  }
  if (caracteres(limpio).some((caracter) => !esLetra(caracter) && !SIMBOLOS.has(caracter))) {
    return 'Usa solo letras, espacios, guiones, apóstrofos, puntos y paréntesis'
  }
  return null
}

/**
 * Deja un nombre con mayúscula solo al inicio: "PASTOR ALEMÁN" queda
 * "Pastor alemán". Un nombre propio conserva su mayúscula si otra palabra quedó
 * en minúscula, como en "Perro sin pelo del Perú".
 */
export function formatearNombreDeCatalogo(texto: string): string {
  const palabras = palabrasDe(texto)
  const primera = palabras.at(0)
  if (primera === undefined) {
    return ''
  }
  const resto = palabras.slice(1)
  const aProposito = resto.some(
    (palabra) => palabra === palabra.toLowerCase() && letras(palabra) !== '',
  )
  const siguientes = resto.map((palabra) => {
    const minuscula = palabra.toLowerCase()
    const conserva = aProposito && !CONECTORES.has(minuscula) && empiezaConMayuscula(palabra)
    return conserva ? palabra : minuscula
  })
  return [mayusculaInicial(primera.toLowerCase()), ...siguientes].join(' ')
}

/** Lo mínimo de un nombre ya cargado para compararlo. */
export interface NombreDelCatalogo {
  readonly name: string
  readonly is_active: boolean
}

export interface Coincidencias<T extends NombreDelCatalogo> {
  /** El mismo nombre salvo tildes, mayúsculas o espacios: el servidor no lo dejaría entrar. */
  readonly exacto: T | undefined
  readonly parecidos: readonly T[]
}

// Con menos letras, cualquier nombre se parecería a muchos otros.
const MIN_LETRAS_PARA_BUSCAR = 3
const MIN_LETRAS_DE_PALABRA = 4
const MAX_PARECIDOS = 6

/** La misma comparación que usa el servidor: sin tildes, sin mayúsculas y sin espacios de más. */
export function claveDeCatalogo(texto: string): string {
  return palabrasDe(texto.normalize('NFD').replace(/\p{M}/gu, '').toLowerCase()).join(' ')
}

function soloLetras(texto: string): string {
  return texto.replace(/[^\p{L}]/gu, '')
}

function palabrasLargas(clave: string): string[] {
  return clave
    .split(' ')
    .map(soloLetras)
    .filter((palabra) => palabra.length >= MIN_LETRAS_DE_PALABRA)
}

// Qué tan parecido es: 0 si, escritos juntos, uno contiene al otro ("pit bull"
// y "Pitbull"); 1 si solo comparten una palabra o una empieza como la otra
// ("terrier" y "Bull terrier"); `null` si no se parecen. Lo más parecido va
// primero, así una palabra común como "bull" no tapa la coincidencia buena.
function nivelDeParecido(nombre: string, buscada: string, palabras: readonly string[]): number | null {
  const clave = claveDeCatalogo(nombre)
  const juntas = soloLetras(clave)
  if (juntas.includes(buscada) || buscada.includes(juntas)) {
    return 0
  }
  const suyas = palabrasLargas(clave)
  const compartida = palabras.some((palabra) =>
    suyas.some((suya) => suya.startsWith(palabra) || palabra.startsWith(suya)),
  )
  return compartida ? 1 : null
}

/** Lo que ya está cargado y se parece a lo que se escribe, lo más parecido primero. */
export function buscarCoincidencias<T extends NombreDelCatalogo>(
  texto: string,
  existentes: readonly T[],
): Coincidencias<T> {
  const clave = claveDeCatalogo(texto)
  const buscada = soloLetras(clave)
  if (buscada.length < MIN_LETRAS_PARA_BUSCAR) {
    return { exacto: undefined, parecidos: [] }
  }
  const exacto = existentes.find((existente) => claveDeCatalogo(existente.name) === clave)
  const palabras = palabrasLargas(clave)
  const parecidos = existentes
    .filter((existente) => existente !== exacto)
    .map((existente) => ({ existente, nivel: nivelDeParecido(existente.name, buscada, palabras) }))
    .filter((item): item is { existente: T; nivel: number } => item.nivel !== null)
    .sort((a, b) => a.nivel - b.nivel)
    .slice(0, MAX_PARECIDOS)
    .map((item) => item.existente)
  return { exacto, parecidos }
}
