import { eq } from 'drizzle-orm'
import { workoutSessions, workoutSets } from '../database/schema'
import { normalizeName } from './fuzzyMatch'

export interface PersonalBests {
  bestWeight: { weightKg: number; reps: number | null } | null
  bestDistance: { distanceKm: number } | null
}

/**
 * Best-ever logged weight (with its paired reps) and best-ever distance
 * for an exercise name, across ALL of the user's history -- powers
 * Guided Session's "beat your own record" target. Mirrors
 * legacy-flask/app/guided.py's _personal_bests, minus duration (this
 * rewrite doesn't have timed/duration-based exercise targets yet).
 */
export function getPersonalBests(userId: number, exerciseName: string): PersonalBests {
  const target = normalizeName(exerciseName)
  const rows = db
    .select({
      exerciseName: workoutSets.exerciseName,
      reps: workoutSets.reps,
      weightKg: workoutSets.weightKg,
      distanceKm: workoutSets.distanceKm,
    })
    .from(workoutSets)
    .innerJoin(workoutSessions, eq(workoutSets.sessionId, workoutSessions.id))
    .where(eq(workoutSessions.userId, userId))
    .all()
    .filter((r) => normalizeName(r.exerciseName) === target)

  let bestWeight: PersonalBests['bestWeight'] = null
  let bestDistance: PersonalBests['bestDistance'] = null
  for (const row of rows) {
    if (row.weightKg !== null && (!bestWeight || row.weightKg > bestWeight.weightKg)) {
      bestWeight = { weightKg: row.weightKg, reps: row.reps }
    }
    if (row.distanceKm !== null && (!bestDistance || row.distanceKm > bestDistance.distanceKm)) {
      bestDistance = { distanceKm: row.distanceKm }
    }
  }
  return { bestWeight, bestDistance }
}
