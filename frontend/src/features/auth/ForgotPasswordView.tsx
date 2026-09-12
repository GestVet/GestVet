import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { Link } from 'react-router'
import { z } from 'zod'

import { forgotPassword } from '../../api/auth'
import FieldError from '../../components/FieldError'
import FormMessage from '../../components/FormMessage'
import Icon from '../../components/Icon'
import { onSubmit } from '../../hooks/formSubmit'
import { errorMessage } from '../../services/api'

const esquema = z.object({
  email: z.email('Ingresá un correo válido'),
})

type Formulario = z.infer<typeof esquema>

export default function ForgotPasswordView() {
  const { register, handleSubmit, formState } = useForm<Formulario>({
    resolver: zodResolver(esquema),
    defaultValues: { email: '' },
  })

  const pedir = useMutation({ mutationFn: forgotPassword })

  return (
    <section className="card form">
      <h1>Recuperar contraseña</h1>
      <p className="muted">
        Ingresá el correo con el que te registraste. Si existe una cuenta, te mandamos un
        enlace para elegir una contraseña nueva.
      </p>

      {pedir.isSuccess ? (
        <FormMessage tone="ok">{pedir.data.message}</FormMessage>
      ) : (
        <form
          className="form"
          onSubmit={onSubmit(
            handleSubmit((valores) => {
              pedir.mutate(valores)
            }),
          )}
        >
          <div className="field">
            <label htmlFor="email">Correo</label>
            <input id="email" type="email" autoComplete="email" {...register('email')} />
            <FieldError message={formState.errors.email?.message} />
          </div>

          {pedir.isError ? (
            <FormMessage tone="error">
              {errorMessage(pedir.error, 'No se pudo procesar el pedido.')}
            </FormMessage>
          ) : null}

          <button type="submit" className="btn btn-blue" disabled={pedir.isPending}>
            <Icon name="confirmar" size={16} />
            <span>{pedir.isPending ? 'Enviando…' : 'Mandar enlace'}</span>
          </button>
        </form>
      )}

      <Link to="/acceso">Volver a iniciar sesión</Link>
    </section>
  )
}
