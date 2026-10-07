import { eq, count } from 'drizzle-orm'
import { programDays } from '../../../database/schema'
import { getOwnedProgram } from '../../../utils/ownership'
import { daySchema } from '../../../utils/validation/programs'

export default defineEventHandler(async (event) => {
  const { user } = await requireUserSession(event)
  const programId = Number(getRouterParam(event, 'id'))
  getOwnedProgram(user.id, programId)

  const body = await readBody(event)
  const parsed = daySchema.safeParse(body)
  if (!parsed.success) {
    throw createError({ statusCode: 400, statusMessage: parsed.error.issues[0].message })
  }

  const [{ value: dayCount }] = db
    .select({ value: count() })
    .from(programDays)
    .where(eq(programDays.programId, programId))
    .all()

  return db
    .insert(programDays)
    .values({ programId, name: parsed.data.name, position: dayCount })
    .returning()
    .get()
})
