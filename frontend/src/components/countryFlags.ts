// Banderas de los países del selector de teléfono.
//
// Son dibujos vectoriales de `country-flag-icons`, no emojis: Windows no
// muestra las banderas emoji y en su lugar escribe las dos letras del país.

import { AR, BO, BR, CL, CO, EC, ES, MX, PE, PY, US, UY, VE } from 'country-flag-icons/react/3x2'

import type { CodigoDePais } from './phoneCountries'

export const BANDERAS: Record<CodigoDePais, typeof PE> = {
  PE,
  AR,
  BO,
  BR,
  CL,
  CO,
  EC,
  ES,
  US,
  MX,
  PY,
  UY,
  VE,
}
