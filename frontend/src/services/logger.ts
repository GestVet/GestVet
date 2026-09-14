import pino, { type Level } from 'pino'

// Logs del navegador.
//
// Pino en su version para navegador escribe con los metodos de la consola, asi
// que en desarrollo cada evento se ve con su objeto expandible. En produccion
// sale como un objeto plano con `time`, `level` y `msg`, que es lo que se copia
// en un reporte. El nivel por defecto cambia con el entorno: en desarrollo se
// ve desde debug; en produccion solo avisos y errores, para no llenar la
// consola de quien usa la aplicacion.
//
// Ningun evento lleva cuerpos de peticion ni tokens: el correo, el DNI o la
// contrasena de una persona no tienen por que quedar en una consola ajena.

const NIVELES: readonly Level[] = ['fatal', 'error', 'warn', 'info', 'debug', 'trace']

function esNivel(valor: string | undefined): valor is Level {
  return NIVELES.some((nivel) => nivel === valor)
}

function nivelConfigurado(): Level {
  const configurado = import.meta.env.VITE_LOG_LEVEL
  if (esNivel(configurado)) {
    return configurado
  }
  return import.meta.env.DEV ? 'debug' : 'warn'
}

export const logger = pino({
  level: nivelConfigurado(),
  serializers: { err: pino.stdSerializers.err },
  browser: {
    asObject: !import.meta.env.DEV,
    serialize: true,
  },
})

/**
 * Registra los errores que nadie capturo.
 *
 * Sin esto, una excepcion en un manejador de eventos o una promesa rechazada
 * sin `catch` solo dejan un mensaje suelto en la consola, sin el formato ni el
 * nivel del resto.
 */
export function logUncaughtErrors(): void {
  window.addEventListener('error', (evento) => {
    const causa: unknown = evento.error
    logger.error(
      { err: causa, source: evento.filename, line: evento.lineno },
      'app.uncaught_error',
    )
  })
  window.addEventListener('unhandledrejection', (evento) => {
    const causa: unknown = evento.reason
    logger.error({ err: causa }, 'app.unhandled_rejection')
  })
}
