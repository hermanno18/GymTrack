import { eq } from 'drizzle-orm'
import { exercises } from '../../database/schema'
import { getOwnedExercise } from '../../utils/ownership'
import { exerciseUpdateSchema } from '../../utils/validation/programs'

export default defineEventHandler(async (event) => {
  const { user } = await requireUserSession(event)
  const exerciseId = Number(getRouterParam(event, 'id'))
  getOwnedExercise(user.id, exerciseId)

  const body = await readBody(event)
  const parsed = exerciseUpdateSchema.safeParse(body)
  if (!parsed.success) {
    throw createError({ statusCode: 400, statusMessage: parsed.error.issues[0].message })
  }

  return db.update(exercises).set(parsed.data).where(eq(exercises.id, exerciseId)).returning().get()
})
