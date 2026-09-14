import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { useState } from 'react'

import { changeRequestsQueryKey, fetchChangeRequests } from '../../api/availability'
import type { UserResponse } from '../../api/types'
import FieldIcon from '../../components/FieldIcon'
import SectionCard from '../../components/SectionCard'
import { NativeSelect, NativeSelectOption } from '../../components/ui/native-select'
import ChangeRequestList from './ChangeRequestList'
import ResolveChangeRequest from './ResolveChangeRequest'

const PENDIENTES = 'pending'

interface TeamChangeRequestsProps {
  readonly veterinarios: readonly UserResponse[]
}

/** Los pedidos de cambio del equipo, con las pendientes primero a la vista. */
export default function TeamChangeRequests({ veterinarios }: TeamChangeRequestsProps) {
  const [estado, setEstado] = useState(PENDIENTES)
  const pedidos = useQuery({
    queryKey: changeRequestsQueryKey(estado),
    queryFn: () => fetchChangeRequests(estado === '' ? undefined : estado),
    placeholderData: keepPreviousData,
  })
  const nombres = new Map(
    veterinarios.map((veterinario) => [
      veterinario.id,
      `${veterinario.first_name} ${veterinario.last_name}`,
    ]),
  )

  return (
    <SectionCard
      collapsible
      scrollable
      title="Pedidos de cambio"
      description="Aceptar no mueve el turno: reasígnalo en el cuadro y deja la respuesta."
      actions={
        <FieldIcon icon="filtro">
        <NativeSelect
          aria-label="Qué pedidos ver"
          className="[&_select]:h-9"
          value={estado}
          onChange={(evento) => {
            setEstado(evento.target.value)
          }}
        >
          <NativeSelectOption value={PENDIENTES}>Pendientes</NativeSelectOption>
          <NativeSelectOption value="">Todos</NativeSelectOption>
        </NativeSelect>
        </FieldIcon>
      }
    >
      <ChangeRequestList
        pedidos={pedidos.data?.items ?? []}
        isLoading={pedidos.isPending}
        emptyMessage={estado === PENDIENTES ? 'No hay pedidos pendientes.' : 'Todavía no hay pedidos.'}
        nombreDe={(id) => nombres.get(id) ?? `Veterinario #${String(id)}`}
        renderActions={(pedido) =>
          pedido.status === PENDIENTES ? <ResolveChangeRequest pedido={pedido} /> : null
        }
      />
    </SectionCard>
  )
}
