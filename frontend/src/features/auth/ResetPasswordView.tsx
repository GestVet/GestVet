import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { useNavigate, useSearchParams } from 'react-router'
import { z } from 'zod'

import { resetPassword } from '../../api/auth'
import FormMessage from '../../components/FormMessage'
import Icon from '../../components/Icon'
import PasswordField from '../../components/PasswordField'
import { Button } from '../../components/ui/button'
import { onSubmit } from '../../hooks/formSubmit'
import { errorMessage } from '../../services/api'
import AuthCard from './AuthCard'
import { MIN_PASSWORD, passwordRule } from '../../services/fieldRules'
import MissingResetToken from './MissingResetToken'

const esquema = z
  .object({
    new_password: passwordRule,
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
    mode: 'onTouched',
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
    return <MissingResetToken />
  }

  return (
    <AuthCard title="Restablecer contraseña">
      {restablecer.isSuccess ? (
        <FormMessage tone="ok">
          {restablecer.data.message} Te llevamos al inicio de sesión…
        </FormMessage>
      ) : (
        <form
          noValidate
          className="flex flex-col gap-5"
          onSubmit={onSubmit(
            handleSubmit((valores) => {
              restablecer.mutate(valores)
            }),
          )}
        >
          <PasswordField
            id="new_password"
            label="Contraseña nueva"
            placeholder="Mínimo 10 caracteres"
            autoComplete="new-password"
            hint={`Al menos ${String(MIN_PASSWORD)} caracteres.`}
            field={register('new_password')}
            error={formState.errors.new_password?.message}
          />

          <PasswordField
            id="confirmacion"
            label="Repite la contraseña"
            placeholder="Escríbela otra vez"
            autoComplete="new-password"
            field={register('confirmacion')}
            error={formState.errors.confirmacion?.message}
          />

          {restablecer.isError ? (
            <FormMessage tone="error">
              {errorMessage(restablecer.error, 'El enlace no es válido o ya venció.')}
            </FormMessage>
          ) : null}

          <Button
            type="submit"
            size="lg"
            className="h-11 w-full"
            disabled={restablecer.isPending}
          >
            <Icon name="confirmar" size={18} />
            <span>{restablecer.isPending ? 'Guardando…' : 'Guardar contraseña'}</span>
          </Button>
        </form>
      )}
    </AuthCard>
  )
}
