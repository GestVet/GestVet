import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'

import { registerStaff, staffQueryKey } from '../../api/directory'
import FormMessage from '../../components/FormMessage'
import Icon from '../../components/Icon'
import SectionCard from '../../components/SectionCard'
import { Button } from '../../components/ui/button'
import { onSubmit } from '../../hooks/formSubmit'
import { errorMessage } from '../../services/api'
import StaffFields from './StaffFields'
import { EMPTY_STAFF_FORM, type StaffFormValues, staffSchema } from './staffSchema'

export default function StaffForm() {
  const queryClient = useQueryClient()
  const { register, handleSubmit, reset, formState } = useForm<StaffFormValues>({
    resolver: zodResolver(staffSchema),
    defaultValues: EMPTY_STAFF_FORM,
  })

  const alta = useMutation({
    mutationFn: registerStaff,
    onSuccess: async () => {
      reset(EMPTY_STAFF_FORM)
      await queryClient.invalidateQueries({ queryKey: staffQueryKey })
    },
  })

  return (
    <SectionCard title="Dar de alta un veterinario">
      <form
        noValidate
        className="flex flex-col gap-5"
        onSubmit={onSubmit(
          handleSubmit((valores) => {
            alta.mutate(valores)
          }),
        )}
      >
        <StaffFields register={register} errors={formState.errors} />

        {alta.isError ? (
          <FormMessage tone="error">
            {errorMessage(alta.error, 'No se pudo dar de alta la cuenta.')}
          </FormMessage>
        ) : null}

        <Button
          type="submit"
          variant="success"
          size="lg"
          className="h-10 self-start px-4"
          disabled={alta.isPending}
        >
          <Icon name="agregar" size={16} />
          <span>{alta.isPending ? 'Creando…' : 'Dar de alta'}</span>
        </Button>
      </form>
    </SectionCard>
  )
}
