import { eq } from 'drizzle-orm'
import { exercises, programDays, programs, workoutSessions, workoutSets } from '../../database/schema'
import { findSimilarExercise } from '../../utils/fuzzyMatch'

/**
 * Powers the "Did you mean X?" prompt while building a program. Pools
 * together every exercise name the user has ever used -- both from their
 * program builders and from free-form workout logs -- so a near-duplicate
 * gets caught no matter where the original name came from.
 */
export default defineEventHandler(async (event) => {
  const { user } = await requireUserSession(event)
  const name = getQuery(event).name
  if (typeof name !== 'string' || !name.trim()) {
    return { match: null }
  }

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

  const candidates = [...new Set([...fromPrograms, ...fromLogs].map((r) => r.name))]
  const match = findSimilarExercise(name, candidates)
  return { match }
})
