import { workoutSessions, workoutSets } from '../../database/schema'
import { getOwnedDay } from '../../utils/ownership'
import { sessionSchema } from '../../utils/validation/sessions'

export default defineEventHandler(async (event) => {
  const { user } = await requireUserSession(event)
  const body = await readBody(event)
  const parsed = sessionSchema.safeParse(body)
  if (!parsed.success) {
    throw createError({ statusCode: 400, statusMessage: parsed.error.issues[0].message })
  }
  const { programDayId, performedAt, exercises: loggedExercises } = parsed.data

  if (programDayId) {
    getOwnedDay(user.id, programDayId) // throws 404 if not owned
  }

  const session = db
    .insert(workoutSessions)
    .values({
      userId: user.id,
      programDayId: programDayId ?? null,
      ...(performedAt ? { performedAt } : {}),
    })
    .returning()
    .get()

  const setRows = loggedExercises.flatMap((ex) =>
    Array.from({ length: ex.sets }, (_, i) => ({
      sessionId: session.id,
      exerciseName: ex.name,
      setNumber: i + 1,
      reps: ex.reps ?? null,
      weightKg: ex.weightKg ?? null,
      distanceKm: ex.distanceKm ?? null,
    })),
  )
  if (setRows.length) {
    db.insert(workoutSets).values(setRows).run()
  }

  return { ok: true, sessionId: session.id }
})
