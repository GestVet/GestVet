import { useState } from 'react'

import FormDialog from '../../components/FormDialog'
import Icon from '../../components/Icon'
import type { IconName } from '../../components/icons'
import { Button } from '../../components/ui/button'
import CatalogEntryForm, { type CatalogEntryFormProps } from './CatalogEntryForm'

interface CatalogEntryDialogButtonProps extends Omit<CatalogEntryFormProps, 'onClose'> {
  readonly buttonLabel: string
  /** Cuando el botón se repite por fila, el nombre de la fila para el lector de pantalla. */
  readonly buttonAriaLabel?: string
  readonly buttonIcon: IconName
  readonly buttonVariant?: 'default' | 'outline'
  readonly dialogTitle: string
  readonly dialogDescription?: string
}

/** Un botón que abre el formulario del catálogo en una ventana. */
export default function CatalogEntryDialogButton({
  buttonLabel,
  buttonAriaLabel,
  buttonIcon,
  buttonVariant = 'default',
  dialogTitle,
  dialogDescription,
  ...formulario
}: CatalogEntryDialogButtonProps) {
  const [abierto, setAbierto] = useState(false)

  return (
    <>
      <Button
        type="button"
        size="sm"
        variant={buttonVariant}
        aria-label={buttonAriaLabel}
        onClick={() => {
          setAbierto(true)
        }}
      >
        <Icon name={buttonIcon} size={14} />
        <span>{buttonLabel}</span>
      </Button>
      <FormDialog
        open={abierto}
        onOpenChange={setAbierto}
        title={dialogTitle}
        description={dialogDescription}
      >
        <CatalogEntryForm
          {...formulario}
          onClose={() => {
            setAbierto(false)
          }}
        />
      </FormDialog>
    </>
  )
}
