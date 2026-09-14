// Banderas de los países del selector de teléfono.
//
// Son dibujos vectoriales de `country-flag-icons`, no emojis: Windows no
// muestra las banderas emoji y en su lugar escribe las dos letras del país.
// Son todas, y pesan: por eso solo las importa el selector, que se carga
// aparte recién cuando aparece un campo de teléfono.

import * as banderas from 'country-flag-icons/react/3x2'
import type { FlagComponent } from 'country-flag-icons/react/3x2'

import type { CodigoDePais } from './phoneCountries'

export const BANDERAS: Readonly<Record<CodigoDePais, FlagComponent>> = banderas
