import { api } from '../services/api'
import type { SubmitReviewRequest, VeterinarianReviewsResponse } from './types'

export function veterinarianReviewsQueryKey(veterinarianId: number) {
  return ['reviews', veterinarianId] as const
}

export async function fetchVeterinarianReviews(
  veterinarianId: number,
): Promise<VeterinarianReviewsResponse> {
  const { data } = await api.get<VeterinarianReviewsResponse>('/reviews', {
    params: { veterinarian_id: veterinarianId },
  })
  return data
}

export async function submitReview(payload: SubmitReviewRequest): Promise<void> {
  await api.post('/reviews', payload)
}
