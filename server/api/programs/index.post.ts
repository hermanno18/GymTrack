import { programs } from '../../database/schema'
import { programSchema } from '../../utils/validation/programs'

export default defineEventHandler(async (event) => {
  const { user } = await requireUserSession(event)
  const body = await readBody(event)
  const parsed = programSchema.safeParse(body)
  if (!parsed.success) {
    throw createError({ statusCode: 400, statusMessage: parsed.error.issues[0].message })
  }

  return db.insert(programs).values({ userId: user.id, name: parsed.data.name }).returning().get()
})
