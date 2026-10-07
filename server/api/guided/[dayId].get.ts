import { exercises } from '../../database/schema'
import { eq } from 'drizzle-orm'
import { getOwnedDay } from '../../utils/ownership'
import { getPersonalBests } from '../../utils/personalBests'

/**
 * Returns everything the client-side guided-session timer needs up
 * front: the day's planned exercises plus, for each, the user's
 * personal-best weight/reps and distance (if any) -- the live timer
 * prefers these over the coach's static target once history exists
 * (see guided/[dayId].vue's effectiveTarget()).
 */
export default defineEventHandler(async (event) => {
  const { user } = await requireUserSession(event)
  const dayId = Number(getRouterParam(event, 'dayId'))
  const day = getOwnedDay(user.id, dayId)

  const dayExercises = db.select().from(exercises).where(eq(exercises.programDayId, day.id)).all()
  if (!dayExercises.length) {
    throw createError({ statusCode: 400, statusMessage: 'This day has no exercises yet -- add some in the program builder first.' })
  }

  const payload = dayExercises
    .sort((a, b) => a.position - b.position)
    .map((ex) => {
      const pr = getPersonalBests(user.id, ex.name)
      return {
        id: ex.id,
        name: ex.name,
        targetSets: ex.targetSets,
        targetReps: ex.targetReps,
        targetWeightKg: ex.targetWeightKg,
        targetDistanceKm: ex.targetDistanceKm,
        prWeightKg: pr.bestWeight?.weightKg ?? null,
        prReps: pr.bestWeight?.reps ?? null,
        prDistanceKm: pr.bestDistance?.distanceKm ?? null,
      }
    })

  return { day: { id: day.id, name: day.name }, exercises: payload }
})
