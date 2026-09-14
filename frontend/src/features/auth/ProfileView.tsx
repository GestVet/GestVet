import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'

import { updateProfile } from '../../api/auth'
import type { UserResponse } from '../../api/types'
import FormMessage from '../../components/FormMessage'
import Icon from '../../components/Icon'
import PageHeader from '../../components/PageHeader'
import SectionCard from '../../components/SectionCard'
import { Button } from '../../components/ui/button'
import { onSubmit } from '../../hooks/formSubmit'
import { errorMessage } from '../../services/api'
import { useSession } from '../../store/session'
import ProfileFields from './ProfileFields'
import { type ProfileForm, profileSchema } from './profileSchema'

/**
 * Valores de partida del formulario.
 *
 * Vive fuera del componente porque cada `??` cuenta para la complejidad, y
 * cuatro campos con respaldo se comian el presupuesto entero de la vista.
 */
function valoresIniciales(user: UserResponse | null): ProfileForm {
  return {
    first_name: user?.first_name ?? '',
    last_name: user?.last_name ?? '',
    phone: user?.phone ?? '',
    document_id: user?.document_id ?? '',
    new_password: '',
  }
}

export default function ProfileView() {
  const user = useSession((state) => state.user)
  const updateUser = useSession((state) => state.updateUser)

  const { register, handleSubmit, formState } = useForm<ProfileForm>({
    resolver: zodResolver(profileSchema),
    defaultValues: valoresIniciales(user),
  })

  const guardar = useMutation({
    mutationFn: (valores: ProfileForm) =>
      updateProfile({
        first_name: valores.first_name,
        last_name: valores.last_name,
        phone: valores.phone,
        document_id: valores.document_id,
        new_password: valores.new_password === '' ? null : valores.new_password,
      }),
    onSuccess: updateUser,
  })

  const errores = formState.errors

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Mi perfil"
        description={`${user?.email ?? ''} · el correo y el rol no se editan desde aquí.`}
      />

      <SectionCard title="Tus datos">
        <form
          noValidate
          className="flex flex-col gap-5"
          onSubmit={onSubmit(
            handleSubmit((valores) => {
              guardar.mutate(valores)
            }),
          )}
        >
          <ProfileFields register={register} errors={errores} />

          {guardar.isError ? (
            <FormMessage tone="error">
              {errorMessage(guardar.error, 'No se pudo guardar el perfil.')}
            </FormMessage>
          ) : null}
          {guardar.isSuccess ? <FormMessage tone="ok">Perfil actualizado.</FormMessage> : null}

          <Button type="submit" size="lg" className="h-10 self-start px-4" disabled={guardar.isPending}>
            <Icon name="confirmar" size={16} />
            <span>{guardar.isPending ? 'Guardando…' : 'Guardar'}</span>
          </Button>
        </form>
      </SectionCard>
    </div>
  )
}
