interface FieldErrorProps {
  /** Para que el campo lo anuncie con `aria-describedby`. */
  readonly id?: string
  readonly message?: string
}

/**
 * El error de un campo, o nada.
 *
 * Existe para que cada formulario no repita el mismo ternario por campo: eran
 * cinco condicionales por pantalla, y la regla de complejidad los contaba.
 */
export default function FieldError({ id, message }: FieldErrorProps) {
  if (message === undefined) {
    return null
  }
  return (
    <p id={id} className="m-0 text-sm text-destructive">
      {message}
    </p>
  )
}
