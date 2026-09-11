interface FieldErrorProps {
  readonly message?: string
}

/**
 * El error de un campo, o nada.
 *
 * Existe para que cada formulario no repita el mismo ternario por campo: eran
 * cinco condicionales por pantalla, y la regla de complejidad los contaba.
 */
export default function FieldError({ message }: FieldErrorProps) {
  if (message === undefined) {
    return null
  }
  return <span className="field-error">{message}</span>
}
