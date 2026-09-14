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
