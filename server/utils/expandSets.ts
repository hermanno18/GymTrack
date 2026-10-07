interface ExerciseEntry {
  name: string
  sets: number
  reps?: number | null
  weightKg?: number | null
  distanceKm?: number | null
}

interface ExerciseTiming {
  startedAt?: string | null // "HH:MM:SS"
  workSeconds?: number | null
  restSeconds?: number | null
}

/**
 * Turns one "I did N sets of X" summary into N individual workout_sets
 * rows (all sharing the same reps/weight/distance, since neither the
 * manual log form nor Guided Session's quick-entry fields support
 * per-set variation). Shared by manual/ad-hoc logging AND Guided Session
 * finish, so the expansion rule only lives in one place.
 *
 * Optional per-exercise timing (Guided Session only) is stamped on just
 * the first set row -- see schema.ts's workoutSets comment for why.
 */
export function expandExerciseToSetRows(sessionId: number, ex: ExerciseEntry, timing?: ExerciseTiming) {
  return Array.from({ length: ex.sets }, (_, i) => ({
    sessionId,
    exerciseName: ex.name,
    setNumber: i + 1,
    reps: ex.reps ?? null,
    weightKg: ex.weightKg ?? null,
    distanceKm: ex.distanceKm ?? null,
    startedAt: i === 0 ? timing?.startedAt ?? null : null,
    workSeconds: i === 0 ? timing?.workSeconds ?? null : null,
    restSeconds: i === 0 ? timing?.restSeconds ?? null : null,
  }))
}
