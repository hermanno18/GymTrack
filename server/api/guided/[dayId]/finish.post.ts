import { workoutSessions, workoutSets } from '../../../database/schema'
import { getOwnedDay } from '../../../utils/ownership'
import { expandExerciseToSetRows } from '../../../utils/expandSets'
import { guidedFinishSchema, toNumberOrNull } from '../../../utils/validation/guided'

export default defineEventHandler(async (event) => {
  const { user } = await requireUserSession(event)
  const dayId = Number(getRouterParam(event, 'dayId'))
  getOwnedDay(user.id, dayId) // throws 404 if not owned

  const body = await readBody(event)
  const parsed = guidedFinishSchema.safeParse(body)
  if (!parsed.success) {
    throw createError({ statusCode: 400, statusMessage: parsed.error.issues[0].message })
  }
  const { startTime, endTime, results } = parsed.data

  const session = db
    .insert(workoutSessions)
    .values({
      userId: user.id,
      programDayId: dayId,
      startTime: startTime ?? null,
      endTime: endTime ?? null,
    })
    .returning()
    .get()

  const setRows = results.flatMap((r) =>
    expandExerciseToSetRows(
      session.id,
      {
        name: r.name,
        sets: toNumberOrNull(r.sets) || 1,
        reps: toNumberOrNull(r.reps),
        weightKg: toNumberOrNull(r.weightKg),
        distanceKm: toNumberOrNull(r.distanceKm),
      },
      { startedAt: r.startedAt, workSeconds: r.workSeconds, restSeconds: r.restSeconds },
    ),
  )
  if (setRows.length) {
    db.insert(workoutSets).values(setRows).run()
  }

  return { ok: true, sessionId: session.id }
})
