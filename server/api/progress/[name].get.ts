import { eq } from 'drizzle-orm'
import { workoutSessions, workoutSets } from '../../database/schema'
import { normalizeName } from '../../utils/fuzzyMatch'

interface SessionAggregate {
  performedAt: string
  weightMax: number | null
  distanceSum: number | null
  repsMax: number | null
  setsCount: number
}

/**
 * Progression history for one exercise name (case/whitespace-insensitive
 * match, same join key as everywhere else).
 *
 * The legacy app logged one row per exercise per session, so "the"
 * number for that session was unambiguous. This rewrite logs one row
 * PER SET, so turning that back into a single per-session data point
 * needs a deliberate rule per metric:
 *   - weight -> MAX across the session's sets (your best lift that day)
 *   - reps   -> MAX across the session's sets (best single-set rep count)
 *   - distance -> SUM across the session's sets (total covered that day,
 *     e.g. 3x500m row = 1500m -- summing makes more sense than "best set"
 *     for cardio/conditioning work)
 *   - sets   -> COUNT of set rows (how many sets you actually did)
 */
export default defineEventHandler(async (event) => {
  const { user } = await requireUserSession(event)
  const rawName = getRouterParam(event, 'name')
  if (!rawName) throw createError({ statusCode: 400, statusMessage: 'Exercise name is required' })
  const target = normalizeName(decodeURIComponent(rawName))

  const rows = db
    .select({
      sessionId: workoutSets.sessionId,
      performedAt: workoutSessions.performedAt,
      exerciseName: workoutSets.exerciseName,
      reps: workoutSets.reps,
      weightKg: workoutSets.weightKg,
      distanceKm: workoutSets.distanceKm,
    })
    .from(workoutSets)
    .innerJoin(workoutSessions, eq(workoutSets.sessionId, workoutSessions.id))
    .where(eq(workoutSessions.userId, user.id))
    .all()
    .filter((r) => normalizeName(r.exerciseName) === target)

  if (!rows.length) {
    throw createError({ statusCode: 404, statusMessage: 'No history found for that exercise' })
  }
  const displayName = rows[0].exerciseName

  const bySession = new Map<number, SessionAggregate>()
  for (const row of rows) {
    let agg = bySession.get(row.sessionId)
    if (!agg) {
      agg = { performedAt: row.performedAt, weightMax: null, distanceSum: null, repsMax: null, setsCount: 0 }
      bySession.set(row.sessionId, agg)
    }
    agg.setsCount += 1
    if (row.weightKg !== null) agg.weightMax = Math.max(agg.weightMax ?? -Infinity, row.weightKg)
    if (row.distanceKm !== null) agg.distanceSum = (agg.distanceSum ?? 0) + row.distanceKm
    if (row.reps !== null) agg.repsMax = Math.max(agg.repsMax ?? -Infinity, row.reps)
  }

  const sessionsSorted = [...bySession.values()].sort((a, b) => a.performedAt.localeCompare(b.performedAt))

  function buildSeries(label: string, getValue: (s: SessionAggregate) => number | null) {
    const points = sessionsSorted
      .map((s) => ({ date: s.performedAt, value: getValue(s) }))
      .filter((p) => p.value !== null)
    return points.length ? { label, points } : null
  }

  const series = {
    weight: buildSeries('Weight', (s) => s.weightMax),
    distance: buildSeries('Distance', (s) => s.distanceSum),
    reps: buildSeries('Best Reps', (s) => s.repsMax),
    sets: buildSeries('Sets', (s) => s.setsCount),
  }

  // Deliberately NOT converting kg/km to the user's display unit here --
  // every other endpoint in this app returns raw kg/km and lets the
  // client convert (see app/utils/units.ts), so the label and the
  // plotted numbers can never drift out of sync with each other.
  return {
    displayName,
    series,
    history: sessionsSorted,
  }
})
