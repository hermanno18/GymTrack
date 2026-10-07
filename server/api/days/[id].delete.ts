import { eq } from 'drizzle-orm'
import { programDays } from '../../database/schema'
import { getOwnedDay } from '../../utils/ownership'

export default defineEventHandler(async (event) => {
  const { user } = await requireUserSession(event)
  const dayId = Number(getRouterParam(event, 'id'))
  getOwnedDay(user.id, dayId)

  db.delete(programDays).where(eq(programDays.id, dayId)).run()
  return { ok: true }
})
