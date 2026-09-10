import axios from 'axios'

const DEFAULT_BASE_URL = '/api/v1'

// `import.meta.env` llega sin tipar salvo por los tipos de Vite, así que se
// acota aquí y no en cada llamada.
const configuredBaseUrl: string | undefined = import.meta.env.VITE_API_BASE_URL

export const api = axios.create({
  baseURL: configuredBaseUrl ?? DEFAULT_BASE_URL,
  headers: {
    Accept: 'application/json',
    'Content-Type': 'application/json',
  },
})
