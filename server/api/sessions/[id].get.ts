import { eq } from 'drizzle-orm'
import { workoutSessions, workoutSets, programDays } from '../../database/schema'

export default defineEventHandler(async (event) => {
  const { user } = await requireUserSession(event)
  const sessionId = Number(getRouterParam(event, 'id'))

  const session = db.select().from(workoutSessions).where(eq(workoutSessions.id, sessionId)).get()
  if (!session || session.userId !== user.id) {
    throw createError({ statusCode: 404, statusMessage: 'Session not found' })
  }

  const day = session.programDayId
    ? db.select().from(programDays).where(eq(programDays.id, session.programDayId)).get()
    : null

  const sets = db.select().from(workoutSets).where(eq(workoutSets.sessionId, sessionId)).all()

  const exerciseOrder: string[] = []
  const grouped = new Map<string, typeof sets>()
  for (const set of sets) {
    if (!grouped.has(set.exerciseName)) {
      grouped.set(set.exerciseName, [])
      exerciseOrder.push(set.exerciseName)
    }
    grouped.get(set.exerciseName)!.push(set)
  }

  return {
    id: session.id,
    performedAt: session.performedAt,
    dayName: day?.name ?? 'Ad-hoc',
    startTime: session.startTime,
    endTime: session.endTime,
    exercises: exerciseOrder.map((name) => {
      const exerciseSets = grouped.get(name)!
      const first = exerciseSets[0]
      return {
        name,
        sets: exerciseSets,
        // Guided-Session-only timing, stamped on the setNumber=1 row --
        // null for manual/ad-hoc logging (see schema.ts).
        startedAt: first.startedAt,
        workSeconds: first.workSeconds,
        restSeconds: first.restSeconds,
      }
    }),
  }
})
