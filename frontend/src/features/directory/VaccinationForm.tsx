import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'

import {
  fetchVaccineOptions,
  recordVaccination,
  vaccinationCardQueryKey,
  vaccineOptionsQueryKey,
} from '../../api/medicalRecords'
import DialogFormActions from '../../components/DialogFormActions'
import FormMessage from '../../components/FormMessage'
import Icon from '../../components/Icon'
import { Button } from '../../components/ui/button'
import { onSubmit } from '../../hooks/formSubmit'
import { errorMessage } from '../../services/api'
import VaccinationFields from './VaccinationFields'
import { type VaccinationFormValues, vacunaVacia, vaccinationSchema } from './vaccinationSchema'

interface VaccinationFormProps {
  readonly petId: number
  /** Se llama al registrarla o al cancelar: cierra la ventana. */
  readonly onDone: () => void
}

export default function VaccinationForm({ petId, onDone }: VaccinationFormProps) {
  const queryClient = useQueryClient()
  const opciones = useQuery({
    queryKey: vaccineOptionsQueryKey(petId),
    queryFn: () => fetchVaccineOptions(petId),
  })
  const form = useForm<VaccinationFormValues>({
    resolver: zodResolver(vaccinationSchema),
    defaultValues: vacunaVacia(),
  })

  const registro = useMutation({
    mutationFn: (valores: VaccinationFormValues) =>
      recordVaccination({
        pet_id: petId,
        vaccine: valores.vaccine,
        applied_on: valores.applied_on,
        next_due_on: valores.next_due_on === '' ? null : valores.next_due_on,
        product_name: valores.product_name,
        batch: valores.batch,
        notes: valores.notes,
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: vaccinationCardQueryKey(petId) })
      onDone()
    },
  })

  return (
    <form
      noValidate
      className="flex flex-col gap-5"
      onSubmit={onSubmit(
        form.handleSubmit((valores) => {
          registro.mutate(valores)
        }),
      )}
    >
      <VaccinationFields
        form={form}
        opciones={opciones.data?.items ?? []}
        cargando={opciones.isPending}
        petId={petId}
      />

      {registro.isError ? (
        <FormMessage tone="error">
          {errorMessage(registro.error, 'No se pudo registrar la vacuna.')}
        </FormMessage>
      ) : null}

      <DialogFormActions>
        <Button type="button" variant="outline" size="lg" className="h-10 px-4" onClick={onDone}>
          Cancelar
        </Button>
        <Button type="submit" variant="success" size="lg" className="h-10 px-4" disabled={registro.isPending}>
          <Icon name="vacuna" size={16} />
          <span>{registro.isPending ? 'Guardando…' : 'Registrar vacuna'}</span>
        </Button>
      </DialogFormActions>
    </form>
  )
}
