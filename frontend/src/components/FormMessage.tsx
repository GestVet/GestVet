interface FormMessageProps {
  readonly tone: 'error' | 'ok'
  readonly children: React.ReactNode
}

const TONE_CLASSES = {
  error: 'bg-destructive/10 text-destructive',
  ok: 'bg-success/10 text-success',
} as const

/**
 * El resultado de enviar un formulario.
 *
 * Aparece despues de que la persona actuo, lejos de donde mira, asi que se
 * anuncia: un error interrumpe al lector de pantalla y un exito espera turno.
 */
export default function FormMessage({ tone, children }: FormMessageProps) {
  return (
    <p
      role={tone === 'error' ? 'alert' : 'status'}
      className={`m-0 rounded-lg px-3 py-2 text-sm ${TONE_CLASSES[tone]}`}
    >
      {children}
    </p>
  )
}
