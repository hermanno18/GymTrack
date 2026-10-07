import { z } from 'zod'

export const sessionExerciseSchema = z.object({
  name: z.string().trim().min(1, 'Exercise name is required').max(100),
  sets: z.coerce.number().int().positive().default(1),
  reps: z.coerce.number().int().positive().nullable().optional(),
  weightKg: z.coerce.number().positive().nullable().optional(),
  distanceKm: z.coerce.number().positive().nullable().optional(),
})

export const sessionSchema = z.object({
  programDayId: z.coerce.number().int().positive().nullable().optional(),
  performedAt: z.string().trim().min(1).optional(),
  exercises: z.array(sessionExerciseSchema).min(1, 'Log at least one exercise'),
})
