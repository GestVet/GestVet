import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { Link, useNavigate } from 'react-router'

import { login, registerClient } from '../../api/auth'
import FormMessage from '../../components/FormMessage'
import Icon from '../../components/Icon'
import { Button } from '../../components/ui/button'
import { onSubmit } from '../../hooks/formSubmit'
import { errorMessage } from '../../services/api'
import { useSession } from '../../store/session'
import AuthCard from './AuthCard'
import RegisterFields from './RegisterFields'
import { type RegisterForm, registerSchema } from './registerSchema'

export default function RegisterView() {
  const signIn = useSession((state) => state.signIn)
  const navigate = useNavigate()
  const { register, handleSubmit, formState } = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      first_name: '',
      last_name: '',
      email: '',
      phone: '',
      document_id: '',
      password: '',
    },
  })

  const crear = useMutation({
    mutationFn: async (valores: RegisterForm) => {
      await registerClient({ ...valores, phone: valores.phone ?? '' })
      // El alta no devuelve token: se entra con las mismas credenciales.
      return login({ email: valores.email, password: valores.password })
    },
    onSuccess: (respuesta) => {
      signIn(respuesta)
      void navigate('/panel')
    },
  })

  return (
    <AuthCard
      title="Crear una cuenta"
      description="El registro crea una cuenta de cliente."
      footer={
        <p className="m-0 text-muted-foreground">
          ¿Ya tenés cuenta?{' '}
          <Link to="/acceso" className="font-medium text-primary underline underline-offset-4">
            Iniciá sesión
          </Link>
        </p>
      }
    >
      <form
        noValidate
        className="flex flex-col gap-5"
        onSubmit={onSubmit(
          handleSubmit((valores) => {
            crear.mutate(valores)
          }),
        )}
      >
        <RegisterFields register={register} errors={formState.errors} />

        {crear.isError ? (
          <FormMessage tone="error">
            {errorMessage(crear.error, 'No se pudo crear la cuenta.')}
          </FormMessage>
        ) : null}

        <Button
          type="submit"
          variant="success"
          size="lg"
          className="h-10 w-full"
          disabled={crear.isPending}
        >
          <Icon name="agregar" size={16} />
          <span>{crear.isPending ? 'Creando…' : 'Crear cuenta'}</span>
        </Button>
      </form>
    </AuthCard>
  )
}
