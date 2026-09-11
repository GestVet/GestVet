interface FormMessageProps {
  readonly tone: 'error' | 'ok'
  readonly children: React.ReactNode
}

export default function FormMessage({ tone, children }: FormMessageProps) {
  return (
    <p className={tone === 'error' ? 'form-message is-error' : 'form-message is-ok'}>
      {children}
    </p>
  )
}
