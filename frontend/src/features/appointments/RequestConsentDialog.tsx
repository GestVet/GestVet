import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm, useWatch } from 'react-hook-form'

import { consentsQueryKey, requestConsent } from '../../api/consents'
import DialogFormActions from '../../components/DialogFormActions'
import FormDialog from '../../components/FormDialog'
import FormMessage from '../../components/FormMessage'
import { Button } from '../../components/ui/button'
import { onSubmit } from '../../hooks/formSubmit'
import { errorMessage } from '../../services/api'
import RequestConsentFields from './RequestConsentFields'
import {
  emptyRequest,
  type RequestableKind,
  type RequestConsentInput,
  type RequestConsentValues,
  requestConsentSchema,
  toRequestPayload,
} from './requestConsentSchema'

interface RequestConsentDialogProps {
  readonly appointmentId: number
  readonly initialKind: RequestableKind | ''
  readonly onClose: () => void
}

/**
 * Pedir un consentimiento específico sobre la cita, después de evaluar a la mascota.
 *
 * Se monta abierto y se desmonta al cerrar, así cada pedido arranca vacío o
 * con el tipo que trajo el atajo desde la internación.
 */
export default function RequestConsentDialog({
  appointmentId,
  initialKind,
  onClose,
}: RequestConsentDialogProps) {
  const queryClient = useQueryClient()
  const { register, handleSubmit, formState, control } = useForm<
    RequestConsentInput,
    unknown,
    RequestConsentValues
  >({
    resolver: zodResolver(requestConsentSchema),
    defaultValues: emptyRequest(initialKind),
  })
  const kind = useWatch({ control, name: 'kind' })

  const pedir = useMutation({
    mutationFn: (valores: RequestConsentValues) =>
      requestConsent(toRequestPayload(appointmentId, valores)),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: consentsQueryKey })
      onClose()
    },
  })

  return (
    <FormDialog
      open
      onOpenChange={(abierto) => {
        if (!abierto) {
          onClose()
        }
      }}
      title="Solicitar consentimiento"
      description="El responsable lo recibe en su cuenta al instante. También puede firmarlo acá, en tu pantalla."
      size="lg"
    >
      <form
        noValidate
        className="flex flex-col gap-4"
        onSubmit={onSubmit(
          handleSubmit((valores) => {
            pedir.mutate(valores)
          }),
        )}
      >
        <RequestConsentFields register={register} errors={formState.errors} kind={kind} />
        {pedir.isError ? (
          <FormMessage tone="error">
            {errorMessage(pedir.error, 'No se pudo pedir el consentimiento.')}
          </FormMessage>
        ) : null}
        <DialogFormActions>
          <Button type="button" variant="outline" onClick={onClose}>
            Cancelar
          </Button>
          <Button type="submit" variant="success" disabled={pedir.isPending}>
            {pedir.isPending ? 'Enviando…' : 'Solicitar'}
          </Button>
        </DialogFormActions>
      </form>
    </FormDialog>
  )
}
