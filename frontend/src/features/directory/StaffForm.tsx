import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'

import { registerStaff, staffQueryKey } from '../../api/directory'
import DialogFormActions from '../../components/DialogFormActions'
import FormMessage from '../../components/FormMessage'
import Icon from '../../components/Icon'
import { Button } from '../../components/ui/button'
import { onSubmit } from '../../hooks/formSubmit'
import { errorMessage } from '../../services/api'
import StaffFields from './StaffFields'
import { EMPTY_STAFF_FORM, type StaffFormValues, staffSchema } from './staffSchema'

interface StaffFormProps {
  /** Se llama al dar de alta o al cancelar: cierra la ventana. */
  readonly onDone: () => void
}

export default function StaffForm({ onDone }: StaffFormProps) {
  const queryClient = useQueryClient()
  const { register, handleSubmit, formState, control } = useForm<StaffFormValues>({
    resolver: zodResolver(staffSchema),
    defaultValues: EMPTY_STAFF_FORM,
  })

  const alta = useMutation({
    mutationFn: registerStaff,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: staffQueryKey })
      onDone()
    },
  })

  return (
    <form
      noValidate
      className="flex flex-col gap-5"
      onSubmit={onSubmit(
        handleSubmit((valores) => {
          alta.mutate(valores)
        }),
      )}
    >
      <StaffFields register={register} control={control} errors={formState.errors} />

      {alta.isError ? (
        <FormMessage tone="error">
          {errorMessage(alta.error, 'No se pudo dar de alta la cuenta.')}
        </FormMessage>
      ) : null}

      <DialogFormActions>
        <Button type="button" variant="outline" size="lg" className="h-10 px-4" onClick={onDone}>
          Cancelar
        </Button>
        <Button
          type="submit"
          variant="success"
          size="lg"
          className="h-10 px-4"
          disabled={alta.isPending}
        >
          <Icon name="agregar" size={16} />
          <span>{alta.isPending ? 'Creando…' : 'Dar de alta'}</span>
        </Button>
      </DialogFormActions>
    </form>
  )
}
