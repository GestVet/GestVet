import type { FieldErrors, UseFormRegister } from 'react-hook-form'

import SelectField from '../../components/SelectField'
import TextareaField from '../../components/TextareaField'
import TextField from '../../components/TextField'
import { NativeSelectOption } from '../../components/ui/native-select'
import { ETIQUETA_DE_TIPO, type RoleFormValues, TIPOS_DE_CUENTA } from './roleSchema'

interface RoleFieldsProps {
  readonly register: UseFormRegister<RoleFormValues>
  readonly errors: FieldErrors<RoleFormValues>
  readonly isNew: boolean
  readonly isSystem: boolean
}

/**
 * Nombre, tipo de cuenta y descripción de un rol.
 *
 * El tipo solo se elige al crearlo: cambiarlo después dejaría a las cuentas
 * que ya lo tienen con un rol que no les corresponde. Un rol de sistema no se
 * renombra, porque es el que usan por defecto todas las cuentas de su tipo.
 */
export default function RoleFields({ register, errors, isNew, isSystem }: RoleFieldsProps) {
  return (
    <div className="grid gap-5 sm:grid-cols-2">
      {isSystem ? null : (
        <TextField
          id="role-name"
          label="Nombre"
          maxLength={60}
          placeholder="Por ejemplo, Recepción"
          field={register('name')}
          error={errors.name?.message}
        />
      )}
      {isNew ? (
        <SelectField
          id="role-kind"
          label="Tipo de cuenta"
          hint="Define qué permisos puede tener."
          field={register('account_kind')}
        >
          {TIPOS_DE_CUENTA.map((tipo) => (
            <NativeSelectOption key={tipo} value={tipo}>
              {ETIQUETA_DE_TIPO[tipo]}
            </NativeSelectOption>
          ))}
        </SelectField>
      ) : null}
      <div className="sm:col-span-2">
        <TextareaField
          id="role-description"
          label="Descripción"
          rows={2}
          placeholder="Para qué sirve este rol"
          field={register('description')}
          error={errors.description?.message}
        />
      </div>
    </div>
  )
}
