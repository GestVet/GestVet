import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { Link } from 'react-router'
import { z } from 'zod'

import { forgotPassword } from '../../api/auth'
import FormMessage from '../../components/FormMessage'
import Icon from '../../components/Icon'
import TextField from '../../components/TextField'
import { Button } from '../../components/ui/button'
import { onSubmit } from '../../hooks/formSubmit'
import { errorMessage } from '../../services/api'
import AuthCard from './AuthCard'
import { correoRule } from '../../services/fieldRules'

const esquema = z.object({
  email: correoRule,
})

type Formulario = z.infer<typeof esquema>

export default function ForgotPasswordView() {
  const { register, handleSubmit, formState } = useForm<Formulario>({
    resolver: zodResolver(esquema),
    mode: 'onTouched',
    defaultValues: { email: '' },
  })

  const pedir = useMutation({ mutationFn: forgotPassword })

  return (
    <AuthCard
      title="Recuperar contraseña"
      description="Escribe el correo con el que te registraste. Si hay una cuenta con ese correo, te enviamos un enlace para elegir una contraseña nueva."
      footer={
        <Link to="/acceso" className="font-medium text-primary underline underline-offset-4">
          Volver a iniciar sesión
        </Link>
      }
    >
      {pedir.isSuccess ? (
        <FormMessage tone="ok">{pedir.data.message}</FormMessage>
      ) : (
        <form
          noValidate
          className="flex flex-col gap-5"
          onSubmit={onSubmit(
            handleSubmit((valores) => {
              pedir.mutate(valores)
            }),
          )}
        >
          <TextField
            id="email"
            label="Correo"
            type="email"
            inputMode="email"
            autoComplete="email"
            spellCheck={false}
            field={register('email')}
            error={formState.errors.email?.message}
          />

          {pedir.isError ? (
            <FormMessage tone="error">
              {errorMessage(pedir.error, 'No se pudo enviar el enlace. Inténtalo de nuevo.')}
            </FormMessage>
          ) : null}

          <Button type="submit" size="lg" className="h-11 w-full" disabled={pedir.isPending}>
            <Icon name="correo" size={18} />
            <span>{pedir.isPending ? 'Enviando…' : 'Enviar enlace'}</span>
          </Button>
        </form>
      )}
    </AuthCard>
  )
}
