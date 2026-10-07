import { z } from 'zod'

const numericLike = z.union([z.number(), z.string()]).nullable().optional()

/**
 * weightKg/distanceKm (not "weight"/"distance") deliberately matches the
 * manual-logging contract in validation/sessions.ts -- the client always
 * converts display units -> kg/km before sending, server never touches
 * unit conversion. One contract, not two.
 */
export const guidedResultSchema = z.object({
  name: z.string().trim().min(1),
  startedAt: z.string().nullable().optional(),
  workSeconds: z.number().int().min(0).default(0),
  restSeconds: z.number().int().min(0).default(0),
  sets: numericLike,
  reps: numericLike,
  weightKg: numericLike,
  distanceKm: numericLike,
})

export const guidedFinishSchema = z.object({
  startTime: z.string().nullable().optional(),
  endTime: z.string().nullable().optional(),
  results: z.array(guidedResultSchema).min(1),
})

export function toNumberOrNull(value: unknown): number | null {
  if (value === null || value === undefined || value === '') return null
  const num = Number(value)
  return Number.isFinite(num) ? num : null
}
