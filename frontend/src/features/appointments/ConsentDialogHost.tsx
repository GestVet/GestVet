import type { ConsentDialog } from './consentDialog'
import InPersonSignDialog from './InPersonSignDialog'
import RequestConsentDialog from './RequestConsentDialog'
import WaiveConsentDialog from './WaiveConsentDialog'

interface ConsentDialogHostProps {
  readonly appointmentId: number
  readonly dialog: ConsentDialog | null
  readonly onClose: () => void
}

/** La ventana abierta del panel de consentimientos. */
export default function ConsentDialogHost({ appointmentId, dialog, onClose }: ConsentDialogHostProps) {
  if (dialog === null) {
    return null
  }
  if (dialog.tipo === 'firmar') {
    return <InPersonSignDialog consent={dialog.consent} onClose={onClose} />
  }
  if (dialog.tipo === 'eximir') {
    return (
      <WaiveConsentDialog appointmentId={appointmentId} initialKind={dialog.kind} onClose={onClose} />
    )
  }
  return (
    <RequestConsentDialog appointmentId={appointmentId} initialKind={dialog.kind} onClose={onClose} />
  )
}
