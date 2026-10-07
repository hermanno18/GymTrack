import { eq, asc, inArray } from 'drizzle-orm'
import { programs, programDays } from '../../database/schema'

export default defineEventHandler(async (event) => {
  const { user } = await requireUserSession(event)

  const userPrograms = db.select().from(programs).where(eq(programs.userId, user.id)).all()
  const programIds = userPrograms.map((p) => p.id)

  const days = programIds.length
    ? db.select().from(programDays).where(inArray(programDays.programId, programIds)).orderBy(asc(programDays.position)).all()
    : []

  return userPrograms.map((program) => ({
    ...program,
    days: days.filter((d) => d.programId === program.id).map(({ id, name }) => ({ id, name })),
  }))
})
