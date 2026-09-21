/**
 * Guarda en el equipo un archivo que llegó de la API.
 *
 * El navegador no deja descargar la respuesta de una petición autenticada con
 * un enlace común: se arma un enlace temporal al contenido y se lo pulsa.
 */
export function guardarArchivo(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

// Lo que tarda en cargarse el archivo en la pestaña nueva. Revocar antes deja
// la pestaña en blanco; no revocar retiene el archivo hasta cerrar la sesión.
const VIDA_DEL_ENLACE_MS = 60_000

/**
 * Abre una pestaña vacía para mostrar después un archivo de la API.
 *
 * Se llama dentro del clic, antes de pedir el archivo: el navegador bloquea
 * como ventana emergente cualquier pestaña que se abra después de esperar una
 * respuesta.
 */
export function reservarPestana(): Window | null {
  const pestana = window.open('', '_blank')
  if (pestana !== null) {
    pestana.opener = null
  }
  return pestana
}

/**
 * Muestra un archivo que llegó de la API en la pestaña reservada.
 *
 * Los adjuntos no tienen una dirección pública: se piden con la sesión y se
 * muestran desde memoria. Si el navegador no dejó abrir la pestaña, se guarda.
 */
export function mostrarArchivo(blob: Blob, filename: string, pestana: Window | null): void {
  if (pestana === null) {
    guardarArchivo(blob, filename)
    return
  }
  const url = URL.createObjectURL(blob)
  pestana.location.href = url
  window.setTimeout(() => {
    URL.revokeObjectURL(url)
  }, VIDA_DEL_ENLACE_MS)
}
