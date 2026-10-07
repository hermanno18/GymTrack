import { eq, count } from 'drizzle-orm'
import { workoutSessions } from '../../database/schema'

export default defineEventHandler(async (event) => {
  const { user } = await requireUserSession(event)

  const [{ value: totalWorkouts }] = db
    .select({ value: count() })
    .from(workoutSessions)
    .where(eq(workoutSessions.userId, user.id))
    .all()

  return { totalWorkouts }
})
