import { eq, asc } from 'drizzle-orm'
import { exercises } from '../../database/schema'
import { getOwnedDay } from '../../utils/ownership'

export default defineEventHandler(async (event) => {
  const { user } = await requireUserSession(event)
  const dayId = Number(getRouterParam(event, 'id'))
  const day = getOwnedDay(user.id, dayId)

  const dayExercises = db
    .select()
    .from(exercises)
    .where(eq(exercises.programDayId, dayId))
    .orderBy(asc(exercises.position))
    .all()

  return { ...day, exercises: dayExercises }
})
