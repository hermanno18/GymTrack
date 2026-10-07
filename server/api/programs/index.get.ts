import { eq, desc } from 'drizzle-orm'
import { programs } from '../../database/schema'

export default defineEventHandler(async (event) => {
  const { user } = await requireUserSession(event)
  return db
    .select()
    .from(programs)
    .where(eq(programs.userId, user.id))
    .orderBy(desc(programs.createdAt))
    .all()
})
