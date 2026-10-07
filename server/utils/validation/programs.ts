import { z } from 'zod'

export const programSchema = z.object({
  name: z.string().trim().min(1, 'Program name is required').max(100),
})

export const daySchema = z.object({
  name: z.string().trim().min(1, 'Day name is required').max(100),
})

export const exerciseSchema = z.object({
  name: z.string().trim().min(1, 'Exercise name is required').max(100),
  targetSets: z.coerce.number().int().positive().nullable().optional(),
  targetReps: z.coerce.number().int().positive().nullable().optional(),
  targetWeightKg: z.coerce.number().positive().nullable().optional(),
  targetDistanceKm: z.coerce.number().positive().nullable().optional(),
})

export const exerciseUpdateSchema = exerciseSchema.partial()
