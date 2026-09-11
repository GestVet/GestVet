interface FormMessageProps {
  readonly tone: 'error' | 'ok'
  readonly children: React.ReactNode
}

/** Aviso de un formulario, en rojo o en verde. */
export default function FormMessage({ tone, children }: FormMessageProps) {
  return (
    <p className={tone === 'error' ? 'form-message is-error' : 'form-message is-ok'}>
      {children}
    </p>
  )
}
