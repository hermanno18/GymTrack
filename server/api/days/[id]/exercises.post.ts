import { eq, count } from 'drizzle-orm'
import { exercises } from '../../../database/schema'
import { getOwnedDay } from '../../../utils/ownership'
import { exerciseSchema } from '../../../utils/validation/programs'

export default defineEventHandler(async (event) => {
  const { user } = await requireUserSession(event)
  const dayId = Number(getRouterParam(event, 'id'))
  getOwnedDay(user.id, dayId)

  const body = await readBody(event)
  const parsed = exerciseSchema.safeParse(body)
  if (!parsed.success) {
    throw createError({ statusCode: 400, statusMessage: parsed.error.issues[0].message })
  }

  const [{ value: exerciseCount }] = db
    .select({ value: count() })
    .from(exercises)
    .where(eq(exercises.programDayId, dayId))
    .all()

  return db
    .insert(exercises)
    .values({ programDayId: dayId, position: exerciseCount, ...parsed.data })
    .returning()
    .get()
})
