import { eq, desc, inArray } from 'drizzle-orm'
import { workoutSessions, workoutSets, programDays } from '../../database/schema'

export default defineEventHandler(async (event) => {
  const { user } = await requireUserSession(event)
  const query = getQuery(event)
  const limit = Math.min(Number(query.limit) || 50, 100)

  const sessions = db
    .select()
    .from(workoutSessions)
    .where(eq(workoutSessions.userId, user.id))
    .orderBy(desc(workoutSessions.performedAt))
    .limit(limit)
    .all()

  if (!sessions.length) return []

  const sessionIds = sessions.map((s) => s.id)
  const dayIds = [...new Set(sessions.map((s) => s.programDayId).filter((id): id is number => id !== null))]

  const days = dayIds.length
    ? db.select().from(programDays).where(inArray(programDays.id, dayIds)).all()
    : []
  const dayNameById = new Map(days.map((d) => [d.id, d.name]))

  const sets = db.select().from(workoutSets).where(inArray(workoutSets.sessionId, sessionIds)).all()
  const namesBySession = new Map<number, Set<string>>()
  for (const s of sets) {
    if (!namesBySession.has(s.sessionId)) namesBySession.set(s.sessionId, new Set())
    namesBySession.get(s.sessionId)!.add(s.exerciseName)
  }

  return sessions.map((session) => ({
    id: session.id,
    performedAt: session.performedAt,
    dayName: session.programDayId ? (dayNameById.get(session.programDayId) ?? 'Ad-hoc') : 'Ad-hoc',
    exerciseCount: namesBySession.get(session.id)?.size ?? 0,
  }))
})
