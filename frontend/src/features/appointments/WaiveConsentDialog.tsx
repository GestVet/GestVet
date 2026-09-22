import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'

import { consentsQueryKey, waiveConsent } from '../../api/consents'
import ConfirmDialog from '../../components/ConfirmDialog'
import DialogFormActions from '../../components/DialogFormActions'
import FormDialog from '../../components/FormDialog'
import FormMessage from '../../components/FormMessage'
import { Button } from '../../components/ui/button'
import { errorMessage } from '../../services/api'
import type { RequestableKind } from './requestConsentSchema'
import WaiveConsentFields from './WaiveConsentFields'
import { type WaiveConsentInput, waiveConsentSchema } from './waiveConsentSchema'

type Formulario = WaiveConsentInput

interface WaiveConsentDialogProps {
  readonly appointmentId: number
  readonly initialKind: RequestableKind | ''
  readonly onClose: () => void
}

/**
 * Dejar constancia de que se atiende sin consentimiento por urgencia vital.
 *
 * Solo se ofrece en una emergencia. La atención que salva la vida nunca
 * espera un papel, pero la decisión queda registrada con su justificación.
 */
export default function WaiveConsentDialog({
  appointmentId,
  initialKind,
  onClose,
}: WaiveConsentDialogProps) {
  const queryClient = useQueryClient()
  const { register, handleSubmit, formState } = useForm<Formulario>({
    resolver: zodResolver(waiveConsentSchema),
    defaultValues: { kind: initialKind, justification: '' },
  })
  const eximir = useMutation({
    mutationFn: (valores: Formulario) =>
      waiveConsent({
        appointment_id: appointmentId,
        kind: valores.kind as RequestableKind,
        justification: valores.justification,
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: consentsQueryKey })
      onClose()
    },
  })
  const registrar = handleSubmit((valores) => {
    eximir.mutate(valores)
  })

  return (
    <FormDialog
      open
      onOpenChange={(abierto) => {
        if (!abierto) {
          onClose()
        }
      }}
      title="Continuar sin consentimiento (urgencia vital)"
      description="Úsalo solo si la vida de la mascota corre peligro y no hay forma de ubicar al responsable."
    >
      <form noValidate className="flex flex-col gap-4">
        <WaiveConsentFields register={register} errors={formState.errors} />
        {eximir.isError ? (
          <FormMessage tone="error">
            {errorMessage(eximir.error, 'No se pudo registrar la atención sin consentimiento.')}
          </FormMessage>
        ) : null}
        <DialogFormActions>
          <Button type="button" variant="outline" onClick={onClose}>
            Cancelar
          </Button>
          <ConfirmDialog
            trigger={
              <Button type="button" variant="destructive" disabled={eximir.isPending}>
                {eximir.isPending ? 'Registrando…' : 'Registrar'}
              </Button>
            }
            title="¿Continuar sin consentimiento?"
            description="Queda registrado a tu nombre, con la justificación, y el responsable lo verá en su cuenta."
            confirmLabel="Continuar sin consentimiento"
            onConfirm={() => {
              void registrar()
            }}
          />
        </DialogFormActions>
      </form>
    </FormDialog>
  )
}
