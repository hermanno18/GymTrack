import { eq } from 'drizzle-orm'
import { exercises, programDays, programs, workoutSessions, workoutSets } from '../../database/schema'
import { normalizeName } from '../../utils/fuzzyMatch'

/**
 * Distinct exercise names the user has ever touched, pooled from both
 * their program builders and their workout logs (same pool used by the
 * fuzzy "did you mean" suggester) -- so an exercise only ever logged
 * ad-hoc still shows up here, not just ones that live in a program.
 */
export default defineEventHandler(async (event) => {
  const { user } = await requireUserSession(event)

  const fromPrograms = db
    .select({ name: exercises.name })
    .from(exercises)
    .innerJoin(programDays, eq(exercises.programDayId, programDays.id))
    .innerJoin(programs, eq(programDays.programId, programs.id))
    .where(eq(programs.userId, user.id))
    .all()

  const fromLogs = db
    .select({ name: workoutSets.exerciseName })
    .from(workoutSets)
    .innerJoin(workoutSessions, eq(workoutSets.sessionId, workoutSessions.id))
    .where(eq(workoutSessions.userId, user.id))
    .all()

  const seen = new Map<string, string>() // normalized -> first-seen display name
  for (const row of [...fromPrograms, ...fromLogs]) {
    const key = normalizeName(row.name)
    if (key && !seen.has(key)) seen.set(key, row.name)
  }

  const names = [...seen.values()].sort((a, b) => a.localeCompare(b))
  return { exercises: names }
})
