import { useState } from 'react'

import { Button } from '../../components/ui/button'
import CustomTimeForm, { type CustomTimeFormProps } from './CustomTimeForm'

type CustomTimeInputProps = Omit<CustomTimeFormProps, 'onCancel'>

/** Una hora exacta, fuera de la grilla de 15 minutos, dentro del turno del veterinario. */
export default function CustomTimeInput(props: CustomTimeInputProps) {
  const [abierto, setAbierto] = useState(false)

  if (abierto) {
    return (
      <CustomTimeForm
        {...props}
        onCancel={() => {
          setAbierto(false)
        }}
      />
    )
  }
  return (
    <Button
      type="button"
      variant="link"
      size="sm"
      className="self-start px-0"
      onClick={() => {
        setAbierto(true)
      }}
    >
      Elegir una hora personalizada
    </Button>
  )
}
