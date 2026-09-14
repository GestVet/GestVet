/**
 * Ids de la ayuda y del error de un campo, y el `aria-describedby` que los une.
 *
 * Los campos de texto, de lista y de texto largo enlazan igual su ayuda y su
 * error: quien usa lector de pantalla los oye al entrar al campo.
 */
export function fieldIds(id: string, hint?: string, error?: string) {
  const hintId = `${id}-ayuda`
  const errorId = `${id}-error`
  const describedBy = [hint === undefined ? '' : hintId, error === undefined ? '' : errorId]
    .filter((value) => value !== '')
    .join(' ')
  return { hintId, errorId, describedBy: describedBy === '' ? undefined : describedBy }
}
