import { useQuery } from '@tanstack/react-query'
import { type Control, type FieldErrors, useController, type UseFormRegister } from 'react-hook-form'

import { fetchSpecialties, specialtiesQueryKey } from '../../api/directory'
import FieldError from '../../components/FieldError'
import PasswordField from '../../components/PasswordField'
import PhoneField from '../../components/PhoneField'
import TextField from '../../components/TextField'
import { soloLetras } from '../../services/fieldRules'
import SpecialtyChecklist from './SpecialtyChecklist'
import type { StaffFormValues } from './staffSchema'

interface StaffFieldsProps {
  readonly register: UseFormRegister<StaffFormValues>
  readonly control: Control<StaffFormValues>
  readonly errors: FieldErrors<StaffFormValues>
}

export default function StaffFields({ register, control, errors }: StaffFieldsProps) {
  const catalogo = useQuery({ queryKey: specialtiesQueryKey, queryFn: fetchSpecialties })
  const especialidades = useController({ control, name: 'specialty_ids' })

  return (
    <div className="flex flex-col gap-5">
      <div className="grid gap-5 sm:grid-cols-2">
        <TextField
          id="first_name"
          label="Nombre"
          placeholder="María"
          icon="perfil"
          sanitize={soloLetras}
          field={register('first_name')}
          error={errors.first_name?.message}
        />
        <TextField
          id="last_name"
          label="Apellido"
          placeholder="Quispe Rojas"
          icon="perfil"
          sanitize={soloLetras}
          field={register('last_name')}
          error={errors.last_name?.message}
        />
        <TextField
          id="email"
          label="Correo"
          placeholder="nombre@correo.com"
          type="email"
          field={register('email')}
          error={errors.email?.message}
        />
        <PhoneField
          id="phone"
          label="Teléfono"
          control={control}
          name="phone"
          error={errors.phone?.message}
        />
        <PasswordField
          id="password"
          label="Contraseña inicial"
          placeholder="Mínimo 10 caracteres"
          autoComplete="new-password"
          hint="Al menos 10 caracteres."
          field={register('password')}
          error={errors.password?.message}
        />
      </div>

      <div className="flex flex-col gap-2">
        <p className="m-0 text-sm font-semibold">Especialidades</p>
        <p className="m-0 text-xs text-muted-foreground">
          Con qué atiende. El cliente las verá al elegir con quién reservar.
        </p>
        {catalogo.isPending ? (
          <p className="m-0 text-sm text-muted-foreground">Cargando especialidades…</p>
        ) : (
          <SpecialtyChecklist
            catalog={catalogo.data ?? { items: [] }}
            value={especialidades.field.value}
            onChange={especialidades.field.onChange}
          />
        )}
        <FieldError id="specialty_ids-error" message={errors.specialty_ids?.message} />
      </div>
    </div>
  )
}
