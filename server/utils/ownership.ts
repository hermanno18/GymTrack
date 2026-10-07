import { eq, and } from 'drizzle-orm'
import { programs, programDays, exercises } from '../database/schema'

/**
 * Ownership-chain helpers. Every program/day/exercise lookup goes through
 * these so multi-user data isolation lives in exactly one place instead of
 * being re-implemented (and potentially forgotten) in every route.
 * Each throws a 404 (not 403) on mismatch -- we don't want to confirm to a
 * user that a resource exists at all if it isn't theirs.
 */

export function getOwnedProgram(userId: number, programId: number) {
  const program = db
    .select()
    .from(programs)
    .where(and(eq(programs.id, programId), eq(programs.userId, userId)))
    .get()
  if (!program) {
    throw createError({ statusCode: 404, statusMessage: 'Program not found' })
  }
  return program
}

export function getOwnedDay(userId: number, dayId: number) {
  const row = db
    .select({ day: programDays, program: programs })
    .from(programDays)
    .innerJoin(programs, eq(programDays.programId, programs.id))
    .where(and(eq(programDays.id, dayId), eq(programs.userId, userId)))
    .get()
  if (!row) {
    throw createError({ statusCode: 404, statusMessage: 'Day not found' })
  }
  return row.day
}

export function getOwnedExercise(userId: number, exerciseId: number) {
  const row = db
    .select({ exercise: exercises, program: programs })
    .from(exercises)
    .innerJoin(programDays, eq(exercises.programDayId, programDays.id))
    .innerJoin(programs, eq(programDays.programId, programs.id))
    .where(and(eq(exercises.id, exerciseId), eq(programs.userId, userId)))
    .get()
  if (!row) {
    throw createError({ statusCode: 404, statusMessage: 'Exercise not found' })
  }
  return row.exercise
}
