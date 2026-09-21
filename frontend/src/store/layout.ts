import { create } from 'zustand'

import {
  deleteLayout,
  fetchLayout,
  saveLayout,
  type DashboardBlockPreference,
} from '../api/layout'
import { errorMessage } from '../services/api'
import { logger } from '../services/logger'

// Lo que se espera antes de mandar los cambios: una racha de arrastres o de
// toques en "subir" se resuelve con una sola peticion.
const DEBOUNCE_MS = 800

export interface LayoutSaveError {
  readonly message: string
  readonly at: number
}

interface LayoutState {
  /** El modo de edicion: muestra los controles y el orden se puede tocar. */
  readonly editMode: boolean
  /** Orden preferido del menu. Vacio significa "el orden por defecto". */
  readonly sidebarOrder: readonly string[]
  /** Tarjetas del panel con su visibilidad. Vacio significa "todas visibles". */
  readonly dashboardBlocks: readonly DashboardBlockPreference[]
  /** Hay una personalizacion guardada en el servidor. */
  readonly hasSaved: boolean
  readonly saving: boolean
  /** Lo consume el armazon para avisar con un toast. */
  readonly saveError: LayoutSaveError | null
  toggleEditMode: () => void
  setSidebarOrder: (ids: readonly string[]) => void
  setDashboardBlocks: (blocks: readonly DashboardBlockPreference[]) => void
  reset: () => Promise<void>
  load: () => Promise<void>
  clear: () => void
  clearSaveError: () => void
}

// La cola serializa los PUT: el estado que viaja en cada uno es el que habia al
// encolarlo, asi que dos peticiones nunca se pisan por llegar desordenadas.
let cola: Promise<void> = Promise.resolve()
const temporizador: { id: ReturnType<typeof setTimeout> | undefined } = { id: undefined }
let pendiente = false

function cancelarPendiente(): void {
  clearTimeout(temporizador.id)
  temporizador.id = undefined
  pendiente = false
}

function enviar(): void {
  const estado = useLayoutStore.getState()
  const payload = {
    sidebar_order: [...estado.sidebarOrder],
    dashboard_blocks: [...estado.dashboardBlocks],
  }
  pendiente = false
  useLayoutStore.setState({ saving: true })
  cola = cola.then(async () => {
    try {
      await saveLayout(payload)
      useLayoutStore.setState({ saving: false, hasSaved: true, saveError: null })
    } catch (error) {
      useLayoutStore.setState({
        saving: false,
        saveError: noGuardar(error, 'No se pudo guardar la personalización.', 'layout.save_failed'),
      })
    }
  })
}

function programarEnvio(): void {
  pendiente = true
  clearTimeout(temporizador.id)
  temporizador.id = setTimeout(enviar, DEBOUNCE_MS)
}

/** Confirma lo pendiente sin esperar al debounce; lo llama "Listo". */
function confirmarAhora(): void {
  if (temporizador.id !== undefined) {
    clearTimeout(temporizador.id)
    temporizador.id = undefined
  }
  if (pendiente) {
    enviar()
  }
}

function noGuardar(error: unknown, fallback: string, evento: string): LayoutSaveError {
  logger.warn({ err: error }, evento)
  return { message: errorMessage(error, fallback), at: Date.now() }
}

/**
 * La personalizacion del panel y del menu de la cuenta con sesion.
 *
 * El estado local manda: cada cambio se aplica al instante y el guardado sale
 * detras, con debounce. Si la API falla, se conserva lo local y el armazon
 * avisa con un toast; el proximo cambio vuelve a intentar con el estado
 * completo. Al cerrar la sesion, `clear` deja el estado como recien instalado.
 */
export const useLayoutStore = create<LayoutState>((set, get) => ({
  editMode: false,
  sidebarOrder: [],
  dashboardBlocks: [],
  hasSaved: false,
  saving: false,
  saveError: null,

  toggleEditMode: () => {
    if (get().editMode) {
      confirmarAhora()
    }
    set((state) => ({ editMode: !state.editMode }))
  },

  setSidebarOrder: (ids) => {
    set({ sidebarOrder: [...ids] })
    programarEnvio()
  },

  setDashboardBlocks: (blocks) => {
    set({ dashboardBlocks: blocks.map((block) => ({ id: block.id, visible: block.visible })) })
    programarEnvio()
  },

  reset: async () => {
    cancelarPendiente()
    // Optimista: la pantalla vuelve a los valores por defecto y despues se
    // borra lo guardado. Si la API falla, lo local se mantiene y se avisa.
    set({ sidebarOrder: [], dashboardBlocks: [], hasSaved: false, saveError: null })
    try {
      await deleteLayout()
    } catch (error) {
      set({ saveError: noGuardar(error, 'No se pudo restablecer la personalización.', 'layout.reset_failed') })
    }
  },

  load: async () => {
    try {
      const data = await fetchLayout()
      set({
        sidebarOrder: [...data.sidebar_order],
        dashboardBlocks: data.dashboard_blocks.map((block) => ({
          id: block.id,
          visible: block.visible,
        })),
        hasSaved:
          data.updated_at !== null ||
          data.sidebar_order.length > 0 ||
          data.dashboard_blocks.length > 0,
      })
    } catch (error) {
      // Sin respuesta se arranca con el orden por defecto: la pantalla sigue
      // siendo util y el primer cambio avisara si el guardado tampoco anda.
      logger.warn({ err: error }, 'layout.load_failed')
    }
  },

  clear: () => {
    cancelarPendiente()
    set({
      editMode: false,
      sidebarOrder: [],
      dashboardBlocks: [],
      hasSaved: false,
      saving: false,
      saveError: null,
    })
  },

  clearSaveError: () => {
    set({ saveError: null })
  },
}))
