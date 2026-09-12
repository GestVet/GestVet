import { z } from 'zod'

import { OTHER_SPECIES_OPTION } from '../../components/petSpecies'

export const walkInEmergencySchema = z
  .object({
    first_name: z.string().min(1, 'Ingresá el nombre'),
    last_name: z.string().min(1, 'Ingresá el apellido'),
    document_id: z.string().regex(/^\d{8}$/, 'El DNI tiene 8 dígitos'),
    phone: z.string().max(32).optional(),
    pet_name: z.string().min(1, 'Ingresá el nombre de la mascota'),
    pet_species: z.string().min(1, 'Elegí la especie'),
    pet_species_other: z.string().optional(),
    description: z.string().max(500).optional(),
  })
  .refine(
    (valores) =>
      valores.pet_species !== OTHER_SPECIES_OPTION || !!valores.pet_species_other?.trim(),
    { message: 'Contanos cuál es', path: ['pet_species_other'] },
  )

export type WalkInEmergencyFormValues = z.infer<typeof walkInEmergencySchema>

export const EMPTY_WALK_IN_EMERGENCY: WalkInEmergencyFormValues = {
  first_name: '',
  last_name: '',
  document_id: '',
  phone: '',
  pet_name: '',
  pet_species: '',
  pet_species_other: '',
  description: '',
}
