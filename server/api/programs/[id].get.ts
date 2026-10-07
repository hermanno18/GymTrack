import { eq, asc, inArray } from 'drizzle-orm'
import { programDays, exercises } from '../../database/schema'
import { getOwnedProgram } from '../../utils/ownership'

export default defineEventHandler(async (event) => {
  const { user } = await requireUserSession(event)
  const programId = Number(getRouterParam(event, 'id'))
  const program = getOwnedProgram(user.id, programId)

  const days = db
    .select()
    .from(programDays)
    .where(eq(programDays.programId, programId))
    .orderBy(asc(programDays.position))
    .all()

  const dayIds = days.map((d) => d.id)
  const allExercises = dayIds.length
    ? db.select().from(exercises).where(inArray(exercises.programDayId, dayIds)).orderBy(asc(exercises.position)).all()
    : []

  return {
    ...program,
    days: days.map((day) => ({
      ...day,
      exercises: allExercises.filter((ex) => ex.programDayId === day.id),
    })),
  }
})
