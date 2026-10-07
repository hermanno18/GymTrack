import { eq } from 'drizzle-orm'
import { programs } from '../../database/schema'
import { getOwnedProgram } from '../../utils/ownership'

export default defineEventHandler(async (event) => {
  const { user } = await requireUserSession(event)
  const programId = Number(getRouterParam(event, 'id'))
  getOwnedProgram(user.id, programId)

  db.delete(programs).where(eq(programs.id, programId)).run()
  return { ok: true }
})
