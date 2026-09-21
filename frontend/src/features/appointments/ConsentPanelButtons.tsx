import { Button } from '../../components/ui/button'
import type { ConsentDialog } from './consentDialog'

interface ConsentPanelButtonsProps {
  /** Si la cita es una emergencia: solo ahí se admite atender sin consentimiento. */
  readonly isEmergency: boolean
  readonly onOpen: (dialog: ConsentDialog) => void
}

/** Pedir un consentimiento y, en una emergencia, continuar sin él. */
export default function ConsentPanelButtons({ isEmergency, onOpen }: ConsentPanelButtonsProps) {
  return (
    <div className="flex flex-wrap gap-2">
      <Button
        type="button"
        variant="success"
        onClick={() => {
          onOpen({ tipo: 'pedir', kind: '' })
        }}
      >
        Solicitar consentimiento
      </Button>
      {isEmergency ? (
        <Button
          type="button"
          variant="outline"
          onClick={() => {
            onOpen({ tipo: 'eximir', kind: '' })
          }}
        >
          Continuar sin consentimiento (urgencia vital)
        </Button>
      ) : null}
    </div>
  )
}
