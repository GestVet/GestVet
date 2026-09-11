import type { SyntheticEvent } from 'react'

/**
 * Adapta el manejador de react-hook-form al atributo `onSubmit`.
 *
 * `handleSubmit` devuelve una promesa y el atributo espera algo que no
 * devuelva nada. Pasarlo directo es un error real: nadie espera esa promesa,
 * asi que un fallo dentro del envio se pierde en silencio. Este envoltorio
 * marca la promesa como deliberadamente ignorada en un solo lugar.
 *
 * Se tipa con `SyntheticEvent` y no con `FormEvent` porque los tipos de React
 * marcaron el segundo como obsoleto.
 */
export function onSubmit(
  handler: (event: SyntheticEvent<HTMLFormElement>) => Promise<unknown>,
): (event: SyntheticEvent<HTMLFormElement>) => void {
  return (event) => {
    void handler(event)
  }
}
