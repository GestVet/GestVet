import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { Link, useNavigate, useSearchParams } from 'react-router'
import { z } from 'zod'

import { resetPassword } from '../../api/auth'
import FieldError from '../../components/FieldError'
import FormMessage from '../../components/FormMessage'
import Icon from '../../components/Icon'
import { onSubmit } from '../../hooks/formSubmit'
import { errorMessage } from '../../services/api'

const MIN_PASSWORD = 10

const esquema = z
  .object({
    new_password: z.string().min(MIN_PASSWORD, `Usá al menos ${String(MIN_PASSWORD)} caracteres`),
    confirmacion: z.string(),
  })
  .refine((valores) => valores.new_password === valores.confirmacion, {
    message: 'Las contraseñas no coinciden',
    path: ['confirmacion'],
  })

type Formulario = z.infer<typeof esquema>

export default function ResetPasswordView() {
  const [parametros] = useSearchParams()
  const token = parametros.get('token') ?? ''
  const navigate = useNavigate()
  const { register, handleSubmit, formState } = useForm<Formulario>({
    resolver: zodResolver(esquema),
    defaultValues: { new_password: '', confirmacion: '' },
  })

  const restablecer = useMutation({
    mutationFn: (valores: Formulario) =>
      resetPassword({ token, new_password: valores.new_password }),
    onSuccess: () => {
      setTimeout(() => {
        void navigate('/acceso')
      }, 2000)
    },
  })

  if (!token) {
    return (
      <section className="card form">
        <h1>Restablecer contraseña</h1>
        <FormMessage tone="error">
          El enlace no trae el código de recuperación. Pedí uno nuevo.
        </FormMessage>
        <Link to="/olvide-contrasena">Pedir un enlace nuevo</Link>
      </section>
    )
  }

  return (
    <section className="card form">
      <h1>Restablecer contraseña</h1>

      {restablecer.isSuccess ? (
        <FormMessage tone="ok">
          {restablecer.data.message} Te llevamos al inicio de sesión…
        </FormMessage>
      ) : (
        <form
          className="form"
          onSubmit={onSubmit(
            handleSubmit((valores) => {
              restablecer.mutate(valores)
            }),
          )}
        >
          <div className="field">
            <label htmlFor="new_password">Contraseña nueva</label>
            <input
              id="new_password"
              type="password"
              autoComplete="new-password"
              {...register('new_password')}
            />
            <FieldError message={formState.errors.new_password?.message} />
          </div>

          <div className="field">
            <label htmlFor="confirmacion">Repetí la contraseña</label>
            <input
              id="confirmacion"
              type="password"
              autoComplete="new-password"
              {...register('confirmacion')}
            />
            <FieldError message={formState.errors.confirmacion?.message} />
          </div>

          {restablecer.isError ? (
            <FormMessage tone="error">
              {errorMessage(restablecer.error, 'El enlace no es válido o ya venció.')}
            </FormMessage>
          ) : null}

          <button type="submit" className="btn btn-blue" disabled={restablecer.isPending}>
            <Icon name="confirmar" size={16} />
            <span>{restablecer.isPending ? 'Guardando…' : 'Guardar contraseña'}</span>
          </button>
        </form>
      )}
    </section>
  )
}
