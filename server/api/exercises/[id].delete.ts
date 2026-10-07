import { eq } from 'drizzle-orm'
import { exercises } from '../../database/schema'
import { getOwnedExercise } from '../../utils/ownership'

export default defineEventHandler(async (event) => {
  const { user } = await requireUserSession(event)
  const exerciseId = Number(getRouterParam(event, 'id'))
  getOwnedExercise(user.id, exerciseId)

  db.delete(exercises).where(eq(exercises.id, exerciseId)).run()
  return { ok: true }
})
